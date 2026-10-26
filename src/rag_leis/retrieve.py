"""Busca de artigos: densa (por significado), BM25 (por palavra), híbrida, reranker e
artigos citados pelo número, combinados a partir de uma configuração."""

import json
import re
from collections.abc import Callable
from functools import lru_cache

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from rag_leis.citacoes import artigos_citados, sem_acento
from rag_leis.dados import artigos_por_id, carregar_corpus
from rag_leis.index import (
    arquivos_do_indice,
    carregar_modelo,
    embutir,
    texto_indexado,
)

# Uma busca recebe a pergunta e quantos artigos quer, e devolve os ids em ordem.
Busca = Callable[[str, int], list[str]]


class Buscador:
    def __init__(self, cabecalho: bool = False) -> None:
        arquivo_indice, arquivo_ids = arquivos_do_indice(cabecalho)
        comando = "python -m rag_leis.index" + (" --cabecalho" if cabecalho else "")
        if not arquivo_indice.exists():
            raise FileNotFoundError(f"Índice não encontrado. Rode: {comando}")
        metadados = json.loads(arquivo_ids.read_text(encoding="utf-8"))
        self.ids: list[str] = metadados["ids"]
        self.indice = faiss.read_index(str(arquivo_indice))
        self.modelo = carregar_modelo(metadados["modelo"])
        self.artigos = artigos_por_id()
        if set(self.ids) != set(self.artigos):
            raise ValueError(f"Índice e corpus não batem. Rode: {comando}")

    def buscar(self, pergunta: str, k: int = 5) -> list[dict]:
        vetor = embutir(self.modelo, [pergunta])
        pontuacoes, posicoes = self.indice.search(vetor, k)
        return [
            {**self.artigos[self.ids[posicao]], "pontuacao": float(pontuacao)}
            for pontuacao, posicao in zip(pontuacoes[0], posicoes[0], strict=True)
        ]


# Palavras que aparecem em quase toda pergunta e todo artigo e só atrapalham o BM25.
_STOPWORDS = """a ao aos as com como da das de do dos e em entre na nas no nos o os ou
para pela pelas pelo pelos por que se sem sua suas seu seus um uma umas uns qual quais
quando onde ser sao foi ha nao mais ja esta este essa esse isso"""
STOPWORDS = frozenset(_STOPWORDS.split())
# Mantém "42-a" junto, para o número de um artigo com letra ser um termo só.
_TERMO = re.compile(r"\d+-[a-z]\b|\w+")


def tokenizar(texto: str) -> list[str]:
    """Minúsculas, sem acento, sem stopwords; números e "42-A" viram termos."""
    return [t for t in _TERMO.findall(sem_acento(texto)) if t not in STOPWORDS]


class BuscadorBM25:
    """Busca por palavra: pontua cada artigo pelos termos da pergunta que ele contém."""

    def __init__(
        self, corpus: list[dict] | None = None, cabecalho: bool = False
    ) -> None:
        corpus = carregar_corpus() if corpus is None else corpus
        self.artigos = corpus
        self.bm25 = BM25Okapi(
            [tokenizar(texto_indexado(registro, cabecalho)) for registro in corpus]
        )

    def buscar(self, pergunta: str, k: int = 5) -> list[dict]:
        pontuacoes = self.bm25.get_scores(tokenizar(pergunta))
        melhores = np.argsort(-pontuacoes, kind="stable")[:k]
        return [
            {**self.artigos[posicao], "pontuacao": float(pontuacoes[posicao])}
            for posicao in melhores
        ]


def fundir_rrf(
    rankings: list[list[str]], c: int = 60, pesos: list[float] | None = None
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion: soma peso / (c + posição) de cada artigo em cada ranking.

    Junta rankings de escalas diferentes (cosseno e BM25) sem calibrar as pontuações.
    O c = 60 é o valor do artigo original (Cormack et al., 2009). Sem pesos, todos valem 1.
    """
    pesos = [1.0] * len(rankings) if pesos is None else pesos
    soma: dict[str, float] = {}
    for ranking, peso in zip(rankings, pesos, strict=True):
        for posicao, artigo in enumerate(ranking, start=1):
            soma[artigo] = soma.get(artigo, 0.0) + peso / (c + posicao)
    return sorted(soma.items(), key=lambda par: -par[1])


# Configuração de busca: os experimentos e o app montam a mesma pipeline a partir dela.
BUSCAS = ("densa", "bm25", "hibrida")
PADRAO = {
    "k": 5,
    "profundidade": 50,
    "rrf_c": 60,
    "pesos": [1.0, 1.0],
    "referencia": False,
    "cabecalho": False,
    "reranker": None,
    "candidatos": 20,
    "split": "dev",
}
MODELO_RERANKER = "BAAI/bge-reranker-v2-m3"
# As duas buscas que o app e o responder oferecem, escolhidas pela tabela de
# experimentos (results/experimentos/tabela.md).
MODOS = {
    "rapida": PADRAO | {"busca": "densa", "cabecalho": True, "referencia": True},
    "completa": PADRAO
    | {
        "busca": "densa",
        "cabecalho": True,
        "referencia": True,
        "reranker": MODELO_RERANKER,
    },
}


# Buscadores e modelos ficam em cache: o app com dois modos e uma rodada de vários
# experimentos usam o mesmo objeto em vez de carregar o modelo de novo.
@lru_cache(maxsize=2)
def buscador_denso(cabecalho: bool) -> Buscador:
    return Buscador(cabecalho)


@lru_cache(maxsize=2)
def buscador_bm25(cabecalho: bool) -> BuscadorBM25:
    return BuscadorBM25(cabecalho=cabecalho)


@lru_cache(maxsize=1)
def _reranker(nome: str):
    from sentence_transformers import CrossEncoder

    return CrossEncoder(nome, device="cpu", max_length=512)


def montar_busca(config: dict) -> Busca:
    """Devolve uma função (pergunta, n) -> n ids, do mais para o menos relevante."""
    if config["busca"] == "bm25":
        bm25 = buscador_bm25(config["cabecalho"])
        return lambda pergunta, n: [a["id"] for a in bm25.buscar(pergunta, n)]

    densa = buscador_denso(config["cabecalho"])
    if config["busca"] == "densa":
        return lambda pergunta, n: [a["id"] for a in densa.buscar(pergunta, n)]

    bm25 = buscador_bm25(config["cabecalho"])

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


def com_reranker(buscar: Busca, config: dict) -> Busca:
    """Reordena os primeiros candidatos com um cross-encoder, que lê pergunta e artigo juntos."""
    textos = {
        registro["id"]: texto_indexado(registro, config["cabecalho"])
        for registro in carregar_corpus()
    }
    modelo = _reranker(config["reranker"])

    def reordenar(pergunta: str, n: int) -> list[str]:
        candidatos = buscar(pergunta, max(n, config["candidatos"]))
        notas = modelo.predict(
            [(pergunta, textos[c]) for c in candidatos], batch_size=4
        )
        ordem = sorted(zip(candidatos, notas, strict=True), key=lambda par: -par[1])
        return [artigo for artigo, _ in ordem][:n]

    return reordenar


def com_referencia(buscar: Busca) -> Busca:
    """Põe na frente os artigos que a pergunta cita pelo número e completa com a busca."""
    ids = {registro["id"] for registro in carregar_corpus()}

    def buscar_citados_primeiro(pergunta: str, n: int) -> list[str]:
        citados = artigos_citados(pergunta, ids)
        resto = [a for a in buscar(pergunta, n + len(citados)) if a not in citados]
        return (citados + resto)[:n]

    return buscar_citados_primeiro


def montar_pipeline(config: dict) -> Callable[[str], list[str]]:
    """Devolve uma função pergunta -> k ids, com as peças que a configuração liga."""
    buscar = montar_busca(config)
    if config["reranker"]:
        buscar = com_reranker(buscar, config)
    if config["referencia"]:
        buscar = com_referencia(buscar)
    return lambda pergunta: buscar(pergunta, config["k"])


def retrieve(pergunta: str, k: int = 5) -> list[dict]:
    """Busca do baseline: os k artigos mais próximos, com a similaridade.

    Fica igual à da fase 3 para o baseline continuar reproduzível; o app e o
    responder usam os MODOS.
    """
    return buscador_denso(False).buscar(pergunta, k)
