"""Responde uma pergunta de ponta a ponta. Uso: python -m rag_leis.responder "sua pergunta"."""

import sys

from rag_leis.generate import generate
from rag_leis.retrieve import retrieve


def responder(pergunta: str, k: int = 5) -> dict:
    artigos = retrieve(pergunta, k)
    return {
        "pergunta": pergunta,
        "artigos": artigos,
        "resposta": generate(pergunta, artigos),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Uso: python -m rag_leis.responder "sua pergunta"')
    saida = responder(sys.argv[1])
    print("Artigos recuperados:")
    for artigo in saida["artigos"]:
        print(f"  {artigo['pontuacao']:.3f}  {artigo['lei']}, art. {artigo['artigo']}")
    print(f"\nResposta:\n{saida['resposta']}")
