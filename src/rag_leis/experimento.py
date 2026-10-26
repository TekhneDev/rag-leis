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

from rag_leis.dados import GOLD, RESULTADOS, ler_jsonl
from rag_leis.evaluate import metricas_de_busca, resumir
from rag_leis.retrieve import BUSCAS, PADRAO, montar_pipeline

RESULTADOS_EXPERIMENTOS = RESULTADOS / "experimentos"
TIPOS = ("geral", "direta", "leiga", "varios_artigos", "termo_exato")


def ler_config(caminho: Path) -> dict:
    """Configuração do arquivo sobre os padrões; recusa chave e busca desconhecidas."""
    lida = json.loads(caminho.read_text(encoding="utf-8"))
    # Uma chave com erro de digitação ("reranquer") seria ignorada em silêncio e o
    # experimento mediria outra coisa; melhor parar.
    desconhecidas = set(lida) - set(PADRAO) - {"busca"}
    if desconhecidas:
        raise ValueError(
            f"chaves desconhecidas em {caminho.name}: {sorted(desconhecidas)}"
        )
    config = PADRAO | lida
    config["nome"] = caminho.stem
    if config["busca"] not in BUSCAS:
        raise ValueError(f"busca deve ser uma de {BUSCAS}, veio {config['busca']!r}")
    return config


def rotulo(config: dict) -> str:
    """Descrição curta do que mudou em relação à busca pura, para a tabela."""
    partes = [config["busca"]]
    if config["cabecalho"]:
        partes[0] += " com cabeçalho"
    if config["busca"] == "hibrida" and config["pesos"] != PADRAO["pesos"]:
        partes[0] += " (pesos " + " / ".join(f"{p:g}" for p in config["pesos"]) + ")"
    if config["reranker"]:
        partes.append(f"reranker nos {config['candidatos']} primeiros")
    if config["referencia"]:
        partes.append("artigo citado primeiro")
    return " + ".join(partes)


def medir_busca(gold: list[dict], recuperados: dict[str, list[str]]) -> list[dict]:
    """Uma linha por pergunta com artigo esperado; fora do escopo não tem o que buscar."""
    return [
        {"id": item["id"], "tipo": item["tipo"]}
        | metricas_de_busca(recuperados[item["id"]], item)
        for item in gold
        if item["artigos_esperados"]
    ]


def rodar(config: dict) -> dict:
    """Busca as perguntas do split, grava as métricas e os ids recuperados."""
    gold = [item for item in ler_jsonl(GOLD) if item["split"] == config["split"]]
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
    RESULTADOS_EXPERIMENTOS.mkdir(parents=True, exist_ok=True)
    destino = RESULTADOS_EXPERIMENTOS / f"{config['nome']}_{config['split']}.json"
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
        for caminho in sorted(RESULTADOS_EXPERIMENTOS.glob("*_dev.json"))
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
    destino = RESULTADOS_EXPERIMENTOS / "tabela.md"
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
