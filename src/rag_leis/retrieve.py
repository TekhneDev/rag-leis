"""Busca densa: traz os artigos cujo vetor está mais próximo do vetor da pergunta."""

import json
from functools import lru_cache

import faiss

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


@lru_cache(maxsize=1)
def _buscador() -> Buscador:
    return Buscador()


def retrieve(pergunta: str, k: int = 5) -> list[dict]:
    """Devolve os k artigos mais próximos da pergunta, do mais para o menos parecido."""
    return _buscador().buscar(pergunta, k)
