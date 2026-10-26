"""Caminhos dos dados e leitura e escrita de arquivos JSONL, um registro por linha."""

import json
import os
from pathlib import Path

# Raiz do repositório, para os comandos funcionarem de qualquer pasta. Numa
# instalação fora do repositório, aponte RAG_LEIS_RAIZ para a pasta do projeto.
RAIZ = Path(os.environ.get("RAG_LEIS_RAIZ", Path(__file__).resolve().parents[2]))
RAW_DIR = RAIZ / "data" / "raw"
CORPUS = RAIZ / "data" / "processed" / "corpus.jsonl"
GOLD = RAIZ / "data" / "gold" / "gold.jsonl"
INDEX_DIR = RAIZ / "data" / "index"
EXPERIMENTOS = RAIZ / "experiments"
RESULTADOS = RAIZ / "results"


def ler_jsonl(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo]


def escrever_linha(arquivo, registro: dict) -> None:
    """Grava um registro e esvazia o buffer, para um processo interrompido não perder nada."""
    arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    arquivo.flush()


def carregar_corpus(caminho: Path = CORPUS) -> list[dict]:
    return ler_jsonl(caminho)


def artigos_por_id() -> dict[str, dict]:
    return {registro["id"]: registro for registro in carregar_corpus()}
