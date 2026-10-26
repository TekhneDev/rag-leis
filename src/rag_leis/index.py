"""Gera o embedding de cada artigo e guarda os vetores num índice FAISS.

Uso:
    python -m rag_leis.index               só o texto do artigo (baseline)
    python -m rag_leis.index --cabecalho   texto precedido de lei, artigo e capítulo
"""

import argparse
import json
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from rag_leis.dados import INDEX_DIR, carregar_corpus

MODELO_EMBEDDING = "BAAI/bge-m3"
ARQUIVO_INDICE = INDEX_DIR / "artigos.faiss"
ARQUIVO_IDS = INDEX_DIR / "artigos.json"
# Nome pelo qual cada lei é conhecida, que o texto do artigo nunca repete.
APELIDOS = {
    "Lei 13.709/2018": "Lei Geral de Proteção de Dados Pessoais, LGPD",
    "Lei 8.078/1990": "Código de Defesa do Consumidor, CDC",
    "Lei 14.133/2021": "Lei de Licitações e Contratos Administrativos",
}


def arquivos_do_indice(cabecalho: bool = False) -> tuple[Path, Path]:
    """Caminho do índice e dos metadados; cada versão do texto tem o seu."""
    if not cabecalho:
        return ARQUIVO_INDICE, ARQUIVO_IDS
    return INDEX_DIR / "artigos_cabecalho.faiss", INDEX_DIR / "artigos_cabecalho.json"


def texto_indexado(registro: dict, cabecalho: bool = False) -> str:
    """O texto que vira vetor. Com cabeçalho, ganha lei, apelido, artigo e capítulo.

    O texto do artigo começa em "Art. 49" mas não diz de qual lei é; o cabeçalho
    dá à busca o que a pergunta costuma citar ("art. 49 do CDC").
    """
    if not cabecalho:
        return registro["texto"]
    partes = [
        f"{registro['lei']} ({APELIDOS[registro['lei']]}), art. {registro['artigo']}"
    ]
    partes += [registro[campo] for campo in ("titulo", "capitulo") if registro[campo]]
    return " · ".join(partes) + "\n" + registro["texto"]


@lru_cache(maxsize=2)
def carregar_modelo(nome: str = MODELO_EMBEDDING) -> SentenceTransformer:
    """Carrega o modelo uma vez por processo; o bge-m3 ocupa uns 2 GB de memória."""
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


def montar_indice(cabecalho: bool = False) -> int:
    """Grava o índice e os metadados e devolve quantos artigos foram indexados."""
    corpus = carregar_corpus()
    modelo = carregar_modelo()
    vetores = embutir(
        modelo,
        [texto_indexado(registro, cabecalho) for registro in corpus],
        progresso=True,
    )

    # Busca exata: para algumas centenas de artigos não é preciso índice aproximado.
    indice = faiss.IndexFlatIP(vetores.shape[1])
    indice.add(vetores)

    arquivo_indice, arquivo_ids = arquivos_do_indice(cabecalho)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(indice, str(arquivo_indice))
    metadados = {
        "modelo": MODELO_EMBEDDING,
        "cabecalho": cabecalho,
        "ids": [registro["id"] for registro in corpus],
    }
    arquivo_ids.write_text(json.dumps(metadados, ensure_ascii=False), encoding="utf-8")
    return len(corpus)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cabecalho", action="store_true")
    args = parser.parse_args()
    print(f"{montar_indice(args.cabecalho)} artigos indexados em {INDEX_DIR}")
