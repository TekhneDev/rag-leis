"""Dados da página de avaliação do app: lê os resultados gravados, só do split dev.

Não roda modelo nenhum. Tudo sai dos arquivos em `results/`, os mesmos que os
comandos de avaliação e de experimento gravam, para a página mostrar só números
que um comando produziu.
"""

import csv
import json
from pathlib import Path

from rag_leis.citacoes import citacoes_fora_dos_trechos
from rag_leis.dados import GOLD, RESULTADOS, ler_jsonl
from rag_leis.evaluate import AMOSTRA_ROTULOS, absteve, metricas_de_busca
from rag_leis.experimento import RESULTADOS_EXPERIMENTOS, TIPOS, rotulo
from rag_leis.retrieve import PADRAO

JUIZ = "gemma3-12b"
# As duas rodadas de ponta a ponta: a busca do baseline e a busca completa do app.
RODADAS = {"baseline": "Baseline (densa)", "completa": "Completa (app)"}
# A ordem em que as peças de busca entraram, cada uma somada à anterior.
EVOLUCAO = [
    ("busca_densa", "Densa (baseline)"),
    ("busca_densa_referencia", "+ artigo citado primeiro"),
    ("busca_densa_cabecalho_referencia", "+ nome da lei no texto (Rápida)"),
    ("busca_densa_cabecalho_reranker_referencia", "+ reranker (Completa)"),
]
NOMES_DOS_TIPOS = {
    "geral": "Geral",
    "direta": "Direta",
    "leiga": "Linguagem leiga",
    "varios_artigos": "Vários artigos",
    "termo_exato": "Termo exato",
    "fora_do_escopo": "Fora do escopo",
}
NOMES_DAS_METRICAS = {
    "recall@1": "Recall@1",
    "recall@3": "Recall@3",
    "recall@5": "Recall@5",
    "mrr": "MRR",
    "acerto@5": "Acerto@5",
    "abstencao_indevida": "Abstenção indevida",
    "abstencao_correta": "Abstenção correta",
    "cita_artigo": "Cita lei e artigo",
    "citacoes_nos_trechos": "Citações só de artigos recebidos",
    "correta": "Correta (juiz)",
    "fiel": "Fiel (juiz)",
}


def metricas_da_rodada(rodada: str, raiz: Path = RESULTADOS) -> dict:
    return json.loads((raiz / rodada / "metricas_dev.json").read_text("utf-8"))


def experimentos(pasta: Path = RESULTADOS_EXPERIMENTOS) -> list[dict]:
    """Um registro por experimento de busca gravado, com a descrição da tabela."""
    registros = []
    for caminho in sorted(pasta.glob("*_dev.json")):
        dados = json.loads(caminho.read_text("utf-8"))
        registros.append(
            {
                "nome": dados["config"]["nome"],
                "descricao": rotulo(PADRAO | dados["config"]),
                "metricas": dados["metricas"],
            }
        )
    return registros


def linhas_de_metrica(metricas: dict, metrica: str) -> list[dict]:
    """Média, intervalo e n de uma métrica em cada tipo de pergunta, na ordem de TIPOS."""
    linhas = []
    for tipo in (*TIPOS, "fora_do_escopo"):
        valor = metricas.get(tipo, {}).get(metrica)
        if valor:
            linhas.append(
                {
                    "tipo": NOMES_DOS_TIPOS[tipo],
                    "media": valor["media"],
                    "baixo": valor["ic95"][0],
                    "alto": valor["ic95"][1],
                    "n": valor["n"],
                }
            )
    return linhas


def evolucao_da_busca(registros: list[dict]) -> list[dict]:
    """Recall@1, recall@5 e MRR gerais em cada etapa de EVOLUCAO."""
    por_nome = {registro["nome"]: registro for registro in registros}
    linhas = []
    for posicao, (nome, etapa) in enumerate(EVOLUCAO, start=1):
        geral = por_nome[nome]["metricas"]["geral"]
        for metrica in ("recall@1", "recall@5", "mrr"):
            linhas.append(
                {
                    "ordem": posicao,
                    "etapa": etapa,
                    "metrica": NOMES_DAS_METRICAS[metrica],
                    "media": geral[metrica]["media"],
                    "baixo": geral[metrica]["ic95"][0],
                    "alto": geral[metrica]["ic95"][1],
                }
            )
    return linhas


def _posicao(recuperados: list[str], esperados: list[str]) -> int | None:
    for posicao, artigo in enumerate(recuperados, start=1):
        if artigo in esperados:
            return posicao
    return None


def por_pergunta(raiz: Path = RESULTADOS, gold: Path = GOLD) -> list[dict]:
    """Uma linha por pergunta do dev, com o que cada rodada recuperou e respondeu.

    As saídas do baseline têm as 75 perguntas; as do test ficam de fora aqui, antes
    de qualquer coisa ser lida, porque o test só é aberto no fim do projeto.
    """
    itens = [item for item in ler_jsonl(gold) if item["split"] == "dev"]
    rodadas = {}
    for rodada in RODADAS:
        saidas = {
            s["id"]: s
            for s in ler_jsonl(raiz / rodada / "saidas.jsonl")
            if s["split"] == "dev"
        }
        julgamentos = {
            j["id"]: j
            for j in ler_jsonl(raiz / rodada / f"julgamentos_{JUIZ}.jsonl")
            if j["id"] in saidas
        }
        rodadas[rodada] = (saidas, julgamentos)
    linhas = []
    for item in itens:
        linha = {"id": item["id"], "tipo": item["tipo"], "pergunta": item["pergunta"]}
        for rodada, (saidas, julgamentos) in rodadas.items():
            saida = saidas[item["id"]]
            linha[f"{rodada}_absteve"] = absteve(saida["resposta"])
            linha[f"{rodada}_correta"] = julgamentos.get(item["id"], {}).get("correta")
            linha[f"{rodada}_fora"] = citacoes_fora_dos_trechos(
                saida["resposta"], saida["recuperados"]
            )
            if item["artigos_esperados"]:
                linha[f"{rodada}_posicao"] = _posicao(
                    saida["recuperados"], item["artigos_esperados"]
                )
                linha[f"{rodada}_recall@5"] = metricas_de_busca(
                    saida["recuperados"], item
                )["recall@5"]
        linhas.append(linha)
    return linhas


def mudancas(linhas: list[dict]) -> dict[str, list[str]]:
    """Perguntas que mudaram de veredito entre o baseline e a completa."""
    resultado = {
        "passou_a_correta": [],
        "deixou_de_ser_correta": [],
        "deixou_de_se_abster": [],
        "passou_a_se_abster": [],
        "cita_fora_dos_trechos": [],
    }
    for linha in linhas:
        if linha["tipo"] == "fora_do_escopo":
            continue
        antes, depois = linha["baseline_correta"], linha["completa_correta"]
        if antes is False and depois is True:
            resultado["passou_a_correta"].append(linha["id"])
        if antes is True and depois is False:
            resultado["deixou_de_ser_correta"].append(linha["id"])
        if linha["baseline_absteve"] and not linha["completa_absteve"]:
            resultado["deixou_de_se_abster"].append(linha["id"])
        if not linha["baseline_absteve"] and linha["completa_absteve"]:
            resultado["passou_a_se_abster"].append(linha["id"])
        if linha["completa_fora"]:
            resultado["cita_fora_dos_trechos"].append(linha["id"])
    return resultado


def estado_do_juiz(pasta: Path = RESULTADOS / "baseline") -> dict:
    """Quantos casos da sonda o juiz acertou e quantos rótulos humanos já existem."""
    sonda = json.loads((pasta / f"sonda_juiz_{JUIZ}.json").read_text("utf-8"))
    with (pasta / "rotulos.csv").open(encoding="utf-8", newline="") as arquivo:
        rotulos = list(csv.DictReader(arquivo))
    preenchidos = sum(
        1 for linha in rotulos if linha["fiel"].strip() and linha["correta"].strip()
    )
    return {
        "sonda": [(caso["caso"], caso["juiz_acertou"]) for caso in sonda],
        "rotulos_preenchidos": preenchidos,
        "rotulos_necessarios": AMOSTRA_ROTULOS,
    }


def numero(valor: float, casas: int = 2) -> str:
    """0.735 -> "0,74", como no resto do projeto."""
    return f"{valor:.{casas}f}".replace(".", ",")
