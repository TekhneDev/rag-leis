"""Busca de artigos: densa (por significado), BM25 (por palavra) e híbrida (as duas)."""

import json
import re
import unicodedata
from functools import lru_cache

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from rag_leis.index import (
    ARQUIVO_IDS,
    ARQUIVO_INDICE,
    carregar_corpus,
    carregar_modelo,
    embutir,
)


class Buscador:
    def __init__(self) -> None:
        if not ARQUIVO_INDICE.exists():
            raise FileNotFoundError(
                "Índice não encontrado. Rode: python -m rag_leis.index"
            )
        metadados = json.loads(ARQUIVO_IDS.read_text(encoding="utf-8"))
        self.ids: list[str] = metadados["ids"]
        self.indice = faiss.read_index(str(ARQUIVO_INDICE))
        self.modelo = carregar_modelo(metadados["modelo"])
        self.artigos = {registro["id"]: registro for registro in carregar_corpus()}
        if set(self.ids) != set(self.artigos):
            raise ValueError(
                "Índice e corpus não batem. Rode: python -m rag_leis.index"
            )

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
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return [t for t in _TERMO.findall(sem_acento) if t not in STOPWORDS]


class BuscadorBM25:
    """Busca por palavra: pontua cada artigo pelos termos da pergunta que ele contém."""

    def __init__(self, corpus: list[dict] | None = None) -> None:
        corpus = carregar_corpus() if corpus is None else corpus
        self.artigos = corpus
        self.bm25 = BM25Okapi([tokenizar(registro["texto"]) for registro in corpus])

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


# Como cada lei costuma ser chamada numa pergunta, já sem acento e em minúsculas.
NOMES_DAS_LEIS = {
    "lgpd": ("13.709", "13709", "lgpd", "lei geral de protecao de dados"),
    "cdc": ("8.078", "8078", "cdc", "codigo de defesa do consumidor"),
    "licitacoes": ("14.133", "14133", "lei de licitacoes", "licitacoes e contratos"),
}
_CITACAO = re.compile(r"\bart(?:igo)?s?\.?\s*(\d+)\s*[ºo°]?(?:\s*-\s*([a-z])\b)?")


def _sem_acento(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def artigos_citados(pergunta: str, ids: set[str]) -> list[str]:
    """Ids dos artigos que a pergunta cita pelo número, como em "art. 75 da Lei 14.133".

    Se a pergunta nomeia uma ou mais leis, só elas contam; se não nomeia nenhuma,
    o número vale para as três. Devolve só ids que existem no corpus.
    """
    texto = _sem_acento(pergunta)
    leis = [
        lei for lei, nomes in NOMES_DAS_LEIS.items() if any(n in texto for n in nomes)
    ]
    leis = leis or list(NOMES_DAS_LEIS)
    citados = []
    for numero, letra in _CITACAO.findall(texto):
        sufixo = f"{numero}-{letra.upper()}" if letra else numero
        for lei in leis:
            artigo = f"{lei}-art-{sufixo}"
            if artigo in ids and artigo not in citados:
                citados.append(artigo)
    return citados


@lru_cache(maxsize=1)
def _buscador() -> Buscador:
    return Buscador()


def retrieve(pergunta: str, k: int = 5) -> list[dict]:
    """Devolve os k artigos mais próximos da pergunta, do mais para o menos parecido."""
    return _buscador().buscar(pergunta, k)
