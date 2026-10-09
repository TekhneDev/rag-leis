"""Gera o embedding de cada artigo e guarda os vetores num índice FAISS."""

import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from rag_leis.chunk import CORPUS

MODELO_EMBEDDING = "BAAI/bge-m3"
INDEX_DIR = Path("data/index")
ARQUIVO_INDICE = INDEX_DIR / "artigos.faiss"
ARQUIVO_IDS = INDEX_DIR / "artigos.json"


def carregar_corpus(caminho: Path = CORPUS) -> list[dict]:
    with caminho.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo]


def carregar_modelo(nome: str = MODELO_EMBEDDING) -> SentenceTransformer:
    return SentenceTransformer(nome, device="cpu")


def embutir(
    modelo: SentenceTransformer, textos: list[str], progresso: bool = False
) -> np.ndarray:
    """Devolve um vetor por texto, com norma 1.

    Com vetores normalizados, o produto interno é a similaridade de cosseno.
    """
    vetores = modelo.encode(
        textos,
        batch_size=4,
        normalize_embeddings=True,
        show_progress_bar=progresso,
    )
    return np.asarray(vetores, dtype="float32")


def montar_indice() -> int:
    corpus = carregar_corpus()
    modelo = carregar_modelo()
    vetores = embutir(
        modelo, [registro["texto"] for registro in corpus], progresso=True
    )

    # Busca exata: para algumas centenas de artigos não é preciso índice aproximado.
    indice = faiss.IndexFlatIP(vetores.shape[1])
    indice.add(vetores)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(indice, str(ARQUIVO_INDICE))
    metadados = {
        "modelo": MODELO_EMBEDDING,
        "ids": [registro["id"] for registro in corpus],
    }
    ARQUIVO_IDS.write_text(json.dumps(metadados, ensure_ascii=False), encoding="utf-8")
    return len(corpus)


if __name__ == "__main__":
    print(f"{montar_indice()} artigos indexados em {INDEX_DIR}")
