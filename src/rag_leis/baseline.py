"""Roda o conjunto ouro inteiro pelo pipeline e salva o que foi recuperado e respondido."""

import json
from pathlib import Path

from rag_leis.generate import MODELO_LLM, generate
from rag_leis.index import MODELO_EMBEDDING
from rag_leis.retrieve import retrieve

GOLD = Path("data/gold/gold.jsonl")
SAIDAS = Path("results/baseline/saidas.jsonl")
K = 5


def _ler(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo]


def rodar(saidas: Path = SAIDAS) -> int:
    """Processa as perguntas que ainda não têm saída; pode ser interrompido e retomado."""
    feitas = {item["id"] for item in _ler(saidas)} if saidas.exists() else set()
    pendentes = [item for item in _ler(GOLD) if item["id"] not in feitas]
    saidas.parent.mkdir(parents=True, exist_ok=True)
    with saidas.open("a", encoding="utf-8") as arquivo:
        for numero, item in enumerate(pendentes, start=1):
            artigos = retrieve(item["pergunta"], K)
            registro = {
                "id": item["id"],
                "tipo": item["tipo"],
                "split": item["split"],
                "pergunta": item["pergunta"],
                "recuperados": [artigo["id"] for artigo in artigos],
                "pontuacoes": [round(artigo["pontuacao"], 4) for artigo in artigos],
                "resposta": generate(item["pergunta"], artigos),
                "modelo_embedding": MODELO_EMBEDDING,
                "modelo_llm": MODELO_LLM,
                "k": K,
            }
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            arquivo.flush()
            print(f"{numero}/{len(pendentes)} {item['id']}", flush=True)
    return len(pendentes)


if __name__ == "__main__":
    print(f"{rodar()} perguntas processadas; saídas em {SAIDAS}")
