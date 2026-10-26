"""Roda o conjunto ouro pelo pipeline e salva o que foi recuperado e respondido.

Uso:
    python -m rag_leis.baseline                    busca do baseline, as 75 perguntas
    python -m rag_leis.baseline --modo completa    um modo do app, só o split dev

Sem --modo, repete a fase 3, que gerou as saídas do baseline antes de existir a
regra de só olhar o dev. Um modo novo roda só no dev; o test fica para o fim.
"""

import argparse
from collections.abc import Callable
from pathlib import Path

from rag_leis.dados import GOLD, RESULTADOS, artigos_por_id, escrever_linha, ler_jsonl
from rag_leis.generate import MODELO_LLM, generate
from rag_leis.index import MODELO_EMBEDDING
from rag_leis.retrieve import MODOS, montar_pipeline, retrieve

SAIDAS = RESULTADOS / "baseline" / "saidas.jsonl"
K = 5


def _busca_do_baseline(pergunta: str) -> tuple[list[dict], dict]:
    artigos = retrieve(pergunta, K)
    pontuacoes = [round(artigo["pontuacao"], 4) for artigo in artigos]
    return artigos, {"pontuacoes": pontuacoes}


def _busca_do_modo(modo: str) -> Callable[[str], tuple[list[dict], dict]]:
    buscar = montar_pipeline(MODOS[modo])
    artigos = artigos_por_id()
    return lambda pergunta: ([artigos[i] for i in buscar(pergunta)], {"modo": modo})


def rodar(
    saidas: Path = SAIDAS, modo: str | None = None, split: str | None = None
) -> int:
    """Processa as perguntas que ainda não têm saída; pode ser interrompido e retomado."""
    feitas = {item["id"] for item in ler_jsonl(saidas)} if saidas.exists() else set()
    pendentes = [
        item
        for item in ler_jsonl(GOLD)
        if item["id"] not in feitas and split in (None, item["split"])
    ]
    buscar = _busca_do_baseline if modo is None else _busca_do_modo(modo)
    saidas.parent.mkdir(parents=True, exist_ok=True)
    with saidas.open("a", encoding="utf-8") as arquivo:
        for numero, item in enumerate(pendentes, start=1):
            artigos, extra = buscar(item["pergunta"])
            registro = {
                "id": item["id"],
                "tipo": item["tipo"],
                "split": item["split"],
                "pergunta": item["pergunta"],
                "recuperados": [artigo["id"] for artigo in artigos],
                **extra,
                "resposta": generate(item["pergunta"], artigos),
                "modelo_embedding": MODELO_EMBEDDING,
                "modelo_llm": MODELO_LLM,
                "k": K,
            }
            escrever_linha(arquivo, registro)
            print(f"{numero}/{len(pendentes)} {item['id']}", flush=True)
    return len(pendentes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--modo", choices=list(MODOS))
    parser.add_argument("--pasta", type=Path, help="padrão: results/<modo>")
    args = parser.parse_args()
    if args.modo is None:
        saidas = SAIDAS
        feitas = rodar(saidas)
    else:
        pasta = args.pasta or RESULTADOS / args.modo
        saidas = pasta / "saidas.jsonl"
        feitas = rodar(saidas, modo=args.modo, split="dev")
    print(f"{feitas} perguntas processadas; saídas em {saidas}")


if __name__ == "__main__":
    main()
