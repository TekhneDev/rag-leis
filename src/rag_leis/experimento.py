"""Roda um experimento de busca descrito num arquivo de configuração e grava as métricas.

Uso:
    python -m rag_leis.experimento experiments/busca_densa.json
    python -m rag_leis.experimento experiments/*.json     vários de uma vez
    python -m rag_leis.experimento --tabela               só refaz a tabela

Só mede a busca (recall, MRR, acerto), que é código puro e não precisa de LLM.
Roda no split dev; o test fica para o fim do projeto, uma única vez.
"""

import argparse
import json
from pathlib import Path

from rag_leis.evaluate import (
    GOLD,
    KS,
    _ler,
    acerto_em_k,
    recall_em_k,
    reciproco_da_posicao,
    resumir,
)

RESULTADOS = Path("results/experimentos")
TIPOS = ("geral", "direta", "leiga", "varios_artigos", "termo_exato")
BUSCAS = ("densa", "bm25", "hibrida")
PADRAO = {
    "k": 5,
    "profundidade": 50,
    "rrf_c": 60,
    "pesos": [1.0, 1.0],
    "referencia": False,
    "reranker": None,
    "candidatos": 20,
    "split": "dev",
}


def ler_config(caminho: Path) -> dict:
    config = PADRAO | json.loads(caminho.read_text(encoding="utf-8"))
    config["nome"] = caminho.stem
    if config["busca"] not in BUSCAS:
        raise ValueError(f"busca deve ser uma de {BUSCAS}, veio {config['busca']!r}")
    return config


def rotulo(config: dict) -> str:
    """Descrição curta do que mudou em relação à busca pura, para a tabela."""
    partes = [config["busca"]]
    if config["busca"] == "hibrida" and config["pesos"] != PADRAO["pesos"]:
        partes[0] += " (pesos " + " / ".join(f"{p:g}" for p in config["pesos"]) + ")"
    if config["reranker"]:
        partes.append(f"reranker nos {config['candidatos']} primeiros")
    if config["referencia"]:
        partes.append("artigo citado primeiro")
    return " + ".join(partes)


def montar_busca(config: dict):
    """Devolve uma função (pergunta, n) -> n ids, do mais para o menos relevante."""
    # Imports aqui dentro: a busca densa carrega o modelo de embedding, que é pesado.
    from rag_leis.retrieve import BuscadorBM25, fundir_rrf

    if config["busca"] == "bm25":
        bm25 = BuscadorBM25()
        return lambda pergunta, n: [a["id"] for a in bm25.buscar(pergunta, n)]

    from rag_leis.retrieve import Buscador

    densa = Buscador()
    if config["busca"] == "densa":
        return lambda pergunta, n: [a["id"] for a in densa.buscar(pergunta, n)]

    bm25 = BuscadorBM25()

    def hibrida(pergunta: str, n: int) -> list[str]:
        # Cada busca traz uma lista mais funda que n, para a fusão ter de onde escolher.
        profundidade = max(n, config["profundidade"])
        rankings = [
            [a["id"] for a in buscador.buscar(pergunta, profundidade)]
            for buscador in (densa, bm25)
        ]
        fundido = fundir_rrf(rankings, config["rrf_c"], config["pesos"])
        return [artigo for artigo, _ in fundido][:n]

    return hibrida


def com_reranker(buscar, config: dict):
    """Reordena os primeiros candidatos com um cross-encoder, que lê pergunta e artigo juntos."""
    from sentence_transformers import CrossEncoder

    from rag_leis.index import carregar_corpus

    textos = {registro["id"]: registro["texto"] for registro in carregar_corpus()}
    modelo = CrossEncoder(config["reranker"], device="cpu", max_length=512)

    def reordenar(pergunta: str, n: int) -> list[str]:
        candidatos = buscar(pergunta, max(n, config["candidatos"]))
        notas = modelo.predict(
            [(pergunta, textos[c]) for c in candidatos], batch_size=4
        )
        ordem = sorted(zip(candidatos, notas, strict=True), key=lambda par: -par[1])
        return [artigo for artigo, _ in ordem][:n]

    return reordenar


def com_referencia(buscar):
    """Põe na frente os artigos que a pergunta cita pelo número e completa com a busca."""
    from rag_leis.index import carregar_corpus
    from rag_leis.retrieve import artigos_citados

    ids = {registro["id"] for registro in carregar_corpus()}

    def buscar_citados_primeiro(pergunta: str, n: int) -> list[str]:
        citados = artigos_citados(pergunta, ids)
        resto = [a for a in buscar(pergunta, n + len(citados)) if a not in citados]
        return (citados + resto)[:n]

    return buscar_citados_primeiro


def montar_pipeline(config: dict):
    buscar = montar_busca(config)
    if config["reranker"]:
        buscar = com_reranker(buscar, config)
    if config["referencia"]:
        buscar = com_referencia(buscar)
    return lambda pergunta: buscar(pergunta, config["k"])


def medir_busca(gold: list[dict], recuperados: dict[str, list[str]]) -> list[dict]:
    """Uma linha por pergunta com artigo esperado; fora do escopo não tem o que buscar."""
    linhas = []
    for item in gold:
        if not item["artigos_esperados"]:
            continue
        ids, esperados = recuperados[item["id"]], item["artigos_esperados"]
        linha = {"id": item["id"], "tipo": item["tipo"]}
        for k in KS:
            linha[f"recall@{k}"] = recall_em_k(ids, esperados, k)
        linha["mrr"] = reciproco_da_posicao(ids, esperados)
        linha["acerto@5"] = acerto_em_k(ids, esperados, item["artigos_aceitos"], 5)
        linhas.append(linha)
    return linhas


def rodar(config: dict) -> dict:
    gold = [item for item in _ler(GOLD) if item["split"] == config["split"]]
    buscar = montar_pipeline(config)
    recuperados = {}
    for item in gold:
        recuperados[item["id"]] = buscar(item["pergunta"])
        print(f"{config['nome']}: {item['id']}", flush=True)
    resultado = {
        "config": config,
        "metricas": resumir(medir_busca(gold, recuperados)),
        "recuperados": recuperados,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    destino = RESULTADOS / f"{config['nome']}_{config['split']}.json"
    destino.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return resultado


def _celula(metricas: dict, tipo: str, metrica: str) -> str:
    valor = metricas.get(tipo, {}).get(metrica)
    return "-" if valor is None else f"{valor['media']:.2f}".replace(".", ",")


def escrever_tabela() -> Path:
    """Junta todos os resultados do dev numa tabela em Markdown."""
    resultados = [
        json.loads(caminho.read_text(encoding="utf-8"))
        for caminho in sorted(RESULTADOS.glob("*_dev.json"))
    ]
    linhas = [
        "# Experimentos de busca (split dev)",
        "",
        "Gerada por `python -m rag_leis.experimento --tabela`. Não edite à mão.",
        "",
        "## Geral",
        "",
        "| Experimento | Configuração | Recall@1 | Recall@3 | Recall@5 | IC 95% do Recall@5 | MRR |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in resultados:
        m, c = r["metricas"], PADRAO | r["config"]
        baixo, alto = (
            f"{v:.2f}".replace(".", ",") for v in m["geral"]["recall@5"]["ic95"]
        )
        linhas.append(
            f"| {c['nome']} | {rotulo(c)} | {_celula(m, 'geral', 'recall@1')} "
            f"| {_celula(m, 'geral', 'recall@3')} | {_celula(m, 'geral', 'recall@5')} "
            f"| {baixo} a {alto} | {_celula(m, 'geral', 'mrr')} |"
        )
    for metrica, titulo in (("recall@5", "Recall@5"), ("mrr", "MRR")):
        linhas += [
            "",
            f"## {titulo} por tipo de pergunta",
            "",
            "| Experimento | " + " | ".join(TIPOS) + " |",
            "| --- |" + " --- |" * len(TIPOS),
        ]
        for r in resultados:
            celulas = " | ".join(_celula(r["metricas"], t, metrica) for t in TIPOS)
            linhas.append(f"| {r['config']['nome']} | {celulas} |")
    destino = RESULTADOS / "tabela.md"
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("configs", nargs="*", type=Path)
    parser.add_argument("--tabela", action="store_true", help="só refaz a tabela")
    args = parser.parse_args()
    for caminho in args.configs:
        config = ler_config(caminho)
        if config["split"] != "dev":
            raise SystemExit(
                "Experimentos rodam no dev. O test é usado uma vez, no fim."
            )
        rodar(config)
    print(f"tabela em {escrever_tabela()}")


if __name__ == "__main__":
    main()
