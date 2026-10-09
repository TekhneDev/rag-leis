"""Mede o pipeline em duas metades: a busca (código puro) e a resposta (LLM como juiz).

Uso:
    python -m rag_leis.evaluate                  métricas de busca e abstenção, split dev
    python -m rag_leis.evaluate --juiz           inclui fidelidade e correção
    python -m rag_leis.evaluate --rotular        gera a amostra para você rotular
    python -m rag_leis.evaluate --concordancia   compara seus rótulos com os do juiz
    python -m rag_leis.evaluate --sondar         testa o juiz com respostas falsas de propósito
    python -m rag_leis.evaluate --split test     só no fim do projeto, uma única vez
"""

import argparse
import csv
import json
import os
import random
from collections import defaultdict
from pathlib import Path

from rag_leis.generate import MODELO_LLM, NAO_ENCONTREI, conversar, montar_prompt
from rag_leis.index import carregar_corpus

GOLD = Path("data/gold/gold.jsonl")
MODELO_JUIZ = os.environ.get("RAG_LEIS_JUIZ", MODELO_LLM)
KS = (1, 3, 5)
AMOSTRA_ROTULOS = 30

JUIZ_FIDELIDADE = """Você avalia se uma resposta sobre legislação está apoiada nos trechos de lei fornecidos.

A resposta é fiel quando toda afirmação de conteúdo que ela faz pode ser confirmada nos trechos.
A resposta não é fiel quando afirma algo que os trechos não dizem ou que contradiz os trechos.
Não avalie se a resposta está completa nem se responde bem à pergunta, só se está apoiada nos trechos.

Responda em JSON: {"justificativa": "uma frase", "fiel": true ou false}"""

JUIZ_CORRECAO = """Você avalia se uma resposta sobre legislação está correta, comparando com a resposta esperada.

A resposta é correta quando traz o mesmo conteúdo essencial da resposta esperada, ainda que com outras palavras ou com mais detalhes.
A resposta não é correta quando contradiz a resposta esperada, omite o ponto principal ou diz que não encontrou.

Responda em JSON: {"justificativa": "uma frase", "correta": true ou false}"""


def _ler(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo]


def recall_em_k(recuperados: list[str], esperados: list[str], k: int) -> float:
    """Fração dos artigos esperados que apareceu entre os k primeiros."""
    return len(set(recuperados[:k]) & set(esperados)) / len(esperados)


def reciproco_da_posicao(recuperados: list[str], esperados: list[str]) -> float:
    """1 dividido pela posição do primeiro artigo esperado; 0 se nenhum apareceu."""
    for posicao, artigo in enumerate(recuperados, start=1):
        if artigo in esperados:
            return 1 / posicao
    return 0.0


def acerto_em_k(
    recuperados: list[str], esperados: list[str], aceitos: list[str], k: int
) -> float:
    """1 se algum artigo esperado ou aceito apareceu entre os k primeiros."""
    return float(bool(set(recuperados[:k]) & (set(esperados) | set(aceitos))))


def absteve(resposta: str) -> bool:
    return NAO_ENCONTREI.rstrip(".").lower() in resposta.lower()


def intervalo_bootstrap(
    valores: list[float], repeticoes: int = 2000
) -> tuple[float, float]:
    """Intervalo de 95% para a média, reamostrando as perguntas com reposição."""
    sorteio = random.Random(42)
    medias = sorted(
        sum(sorteio.choices(valores, k=len(valores))) / len(valores)
        for _ in range(repeticoes)
    )
    return medias[int(0.025 * repeticoes)], medias[int(0.975 * repeticoes) - 1]


def medir(
    gold: list[dict], saidas: list[dict], julgamentos: dict[str, dict]
) -> list[dict]:
    """Uma linha por pergunta, com todas as métricas que se aplicam a ela."""
    por_id = {saida["id"]: saida for saida in saidas}
    linhas = []
    for item in gold:
        saida = por_id[item["id"]]
        linha = {
            "id": item["id"],
            "tipo": item["tipo"],
            "absteve": float(absteve(saida["resposta"])),
        }
        if item["artigos_esperados"]:
            recuperados, esperados = saida["recuperados"], item["artigos_esperados"]
            for k in KS:
                linha[f"recall@{k}"] = recall_em_k(recuperados, esperados, k)
            linha["mrr"] = reciproco_da_posicao(recuperados, esperados)
            linha["acerto@5"] = acerto_em_k(
                recuperados, esperados, item["artigos_aceitos"], 5
            )
        else:
            linha["abstencao_correta"] = linha["absteve"]
        julgamento = julgamentos.get(item["id"], {})
        for metrica in ("fiel", "correta"):
            if metrica in julgamento:
                linha[metrica] = float(julgamento[metrica])
        linhas.append(linha)
    return linhas


def resumir(linhas: list[dict]) -> dict:
    """Média, intervalo e número de perguntas de cada métrica, no geral e por tipo."""
    grupos: dict[str, list[dict]] = defaultdict(list)
    for linha in linhas:
        grupos["geral"].append(linha)
        grupos[linha["tipo"]].append(linha)
    resumo = {}
    for grupo, itens in grupos.items():
        resumo[grupo] = {}
        metricas = sorted({chave for item in itens for chave in item} - {"id", "tipo"})
        for metrica in metricas:
            valores = [item[metrica] for item in itens if metrica in item]
            baixo, alto = intervalo_bootstrap(valores)
            resumo[grupo][metrica] = {
                "media": round(sum(valores) / len(valores), 3),
                "ic95": [round(baixo, 3), round(alto, 3)],
                "n": len(valores),
            }
    return resumo


def _trechos(saida: dict, artigos: dict[str, dict]) -> str:
    return montar_prompt(saida["pergunta"], [artigos[i] for i in saida["recuperados"]])


def _perguntar_ao_juiz(instrucoes: str, conteudo: str, campo: str) -> dict:
    bruto = conversar(instrucoes, conteudo, modelo=MODELO_JUIZ, json=True)
    try:
        return {campo: bool(json.loads(bruto)[campo]), f"justificativa_{campo}": bruto}
    except (json.JSONDecodeError, KeyError):
        return {f"justificativa_{campo}": bruto}


def julgar(gold: list[dict], saidas: list[dict], destino: Path) -> dict[str, dict]:
    """Roda o juiz nas respostas que ainda não foram julgadas; pode ser retomado."""
    feitos = {item["id"]: item for item in _ler(destino)} if destino.exists() else {}
    artigos = {registro["id"]: registro for registro in carregar_corpus()}
    por_id = {saida["id"]: saida for saida in saidas}
    with destino.open("a", encoding="utf-8") as arquivo:
        for item in gold:
            if item["id"] in feitos:
                continue
            saida = por_id[item["id"]]
            julgamento = {"id": item["id"], "juiz": MODELO_JUIZ}
            if item["artigos_esperados"]:
                # Em pergunta fora do escopo, acertar é abster-se; não há o que comparar.
                julgamento |= _perguntar_ao_juiz(
                    JUIZ_CORRECAO,
                    f"Pergunta: {item['pergunta']}\n\nResposta esperada: {item['resposta_esperada']}"
                    f"\n\nResposta a avaliar: {saida['resposta']}",
                    "correta",
                )
            if not absteve(saida["resposta"]):
                julgamento |= _perguntar_ao_juiz(
                    JUIZ_FIDELIDADE,
                    f"{_trechos(saida, artigos)}\n\nResposta a avaliar: {saida['resposta']}",
                    "fiel",
                )
            arquivo.write(json.dumps(julgamento, ensure_ascii=False) + "\n")
            arquivo.flush()
            feitos[item["id"]] = julgamento
            print(f"julgada {item['id']}", flush=True)
    return feitos


def gerar_amostra_para_rotular(
    gold: list[dict], saidas: list[dict], pasta: Path
) -> int:
    """Sorteia respostas do dev para você rotular sem ver a opinião do juiz."""
    artigos = {registro["id"]: registro for registro in carregar_corpus()}
    por_id = {saida["id"]: saida for saida in saidas}
    candidatas = [
        item for item in gold if item["split"] == "dev" and item["artigos_esperados"]
    ]
    amostra = sorted(
        random.Random(42).sample(candidatas, min(AMOSTRA_ROTULOS, len(candidatas))),
        key=lambda item: item["id"],
    )
    leitura = [
        "# Respostas para rotular",
        "",
        "Para cada resposta, preencha em `rotulos.csv`, com `sim` ou `nao`:",
        "",
        "- `fiel`: tudo o que a resposta afirma está nos trechos recuperados?",
        "- `correta`: a resposta traz o conteúdo essencial da resposta esperada?",
        "",
        "Onde o sistema respondeu que não encontrou, `fiel` já vem com `-`: não há afirmação a conferir.",
        "",
        "Rotule antes de olhar os julgamentos do juiz.",
        "",
    ]
    for item in amostra:
        saida = por_id[item["id"]]
        leitura += [
            f"## {item['id']}",
            "",
            f"**Pergunta:** {item['pergunta']}",
            "",
            f"**Resposta esperada:** {item['resposta_esperada']}",
            "",
            f"**Resposta do sistema:** {saida['resposta']}",
            "",
            "**Trechos recuperados:**",
            "",
            "```text",
            _trechos(saida, artigos).rsplit("\n\nPergunta: ", 1)[0],
            "```",
            "",
        ]
    (pasta / "rotular.md").write_text("\n".join(leitura), encoding="utf-8")
    with (pasta / "rotulos.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["id", "fiel", "correta"])
        for item in amostra:
            fiel = "-" if absteve(por_id[item["id"]]["resposta"]) else ""
            escritor.writerow([item["id"], fiel, ""])
    return len(amostra)


def concordancia(pasta: Path) -> dict:
    """Fração das respostas em que o juiz deu o mesmo rótulo que você."""
    julgamentos = {item["id"]: item for item in _ler(pasta / "julgamentos.jsonl")}
    valor = {"sim": True, "nao": False, "não": False}
    resultado = {}
    with (pasta / "rotulos.csv").open(encoding="utf-8", newline="") as arquivo:
        rotulos = list(csv.DictReader(arquivo))
    for metrica in ("fiel", "correta"):
        pares = [
            (valor[linha[metrica].strip().lower()], julgamentos[linha["id"]][metrica])
            for linha in rotulos
            if linha[metrica].strip().lower() in valor
            and metrica in julgamentos.get(linha["id"], {})
        ]
        if pares:
            iguais = sum(humano == juiz for humano, juiz in pares)
            resultado[metrica] = {
                "concordancia": round(iguais / len(pares), 3),
                "n": len(pares),
            }
    return resultado


# Respostas sobre os mesmos cinco artigos do CDC, com o veredito que um bom juiz daria.
ARTIGOS_DA_SONDA = [
    "cdc-art-51",
    "cdc-art-39",
    "cdc-art-37",
    "cdc-art-54",
    "cdc-art-107",
]
SONDA = [
    (
        "apoiada nos trechos",
        (
            "São nulas de pleno direito as cláusulas que transfiram responsabilidades a terceiros "
            "(Lei 8.078/1990, art. 51, III)."
        ),
        True,
    ),
    (
        "prazo inventado",
        (
            "São nulas as cláusulas abusivas, e o consumidor tem 45 dias para pedir a anulação ao "
            "Procon (Lei 8.078/1990, art. 51)."
        ),
        False,
    ),
    (
        "contradiz o trecho",
        (
            "As cláusulas que exonerem a responsabilidade do fornecedor por vícios são válidas e "
            "plenamente eficazes (Lei 8.078/1990, art. 51)."
        ),
        False,
    ),
    (
        "verdadeira, mas de artigo que não foi recuperado",
        (
            "O consumidor pode desistir da compra em 7 dias quando ela é feita fora do "
            "estabelecimento comercial (Lei 8.078/1990, art. 49)."
        ),
        False,
    ),
]


def sondar_juiz() -> list[dict]:
    """Mostra se o juiz de fidelidade consegue reprovar uma resposta que deveria reprovar."""
    artigos = {registro["id"]: registro for registro in carregar_corpus()}
    trechos = montar_prompt(
        "O que é cláusula abusiva?", [artigos[i] for i in ARTIGOS_DA_SONDA]
    )
    resultados = []
    for caso, resposta, esperado in SONDA:
        veredito = _perguntar_ao_juiz(
            JUIZ_FIDELIDADE, f"{trechos}\n\nResposta a avaliar: {resposta}", "fiel"
        )
        resultados.append(
            {
                "caso": caso,
                "resposta": resposta,
                "fiel_esperado": esperado,
                "fiel_juiz": veredito.get("fiel"),
                "juiz_acertou": veredito.get("fiel") == esperado,
                "justificativa": veredito["justificativa_fiel"],
                "juiz": MODELO_JUIZ,
            }
        )
    return resultados


def _imprimir(resumo: dict) -> None:
    for grupo, metricas in resumo.items():
        print(f"\n{grupo}")
        for metrica, valores in metricas.items():
            baixo, alto = valores["ic95"]
            print(
                f"  {metrica:<18} {valores['media']:.3f}  [{baixo:.3f}, {alto:.3f}]  n={valores['n']}"
            )


def main() -> None:
    argumentos = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    argumentos.add_argument("--pasta", type=Path, default=Path("results/baseline"))
    argumentos.add_argument("--split", choices=["dev", "test"], default="dev")
    argumentos.add_argument("--juiz", action="store_true")
    argumentos.add_argument("--rotular", action="store_true")
    argumentos.add_argument("--concordancia", action="store_true")
    argumentos.add_argument("--sondar", action="store_true")
    opcoes = argumentos.parse_args()

    if opcoes.sondar:
        resultados = sondar_juiz()
        destino = opcoes.pasta / "sonda_juiz.json"
        destino.write_text(
            json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for resultado in resultados:
            situacao = "acertou" if resultado["juiz_acertou"] else "ERROU"
            print(f"{situacao:<8} {resultado['caso']}")
        return

    todas = _ler(GOLD)
    saidas = _ler(opcoes.pasta / "saidas.jsonl")
    if opcoes.rotular:
        print(
            f"{gerar_amostra_para_rotular(todas, saidas, opcoes.pasta)} respostas em rotular.md"
        )
        return
    if opcoes.concordancia:
        print(json.dumps(concordancia(opcoes.pasta), ensure_ascii=False, indent=2))
        return

    gold = [item for item in todas if item["split"] == opcoes.split]
    arquivo_julgamentos = opcoes.pasta / "julgamentos.jsonl"
    if opcoes.juiz:
        julgamentos = julgar(gold, saidas, arquivo_julgamentos)
    elif arquivo_julgamentos.exists():
        julgamentos = {item["id"]: item for item in _ler(arquivo_julgamentos)}
    else:
        julgamentos = {}

    resumo = resumir(medir(gold, saidas, julgamentos))
    destino = opcoes.pasta / f"metricas_{opcoes.split}.json"
    destino.write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _imprimir(resumo)
    print(f"\nGravado em {destino}")


if __name__ == "__main__":
    main()
