"""Responde uma pergunta de ponta a ponta, com a mesma busca do app.

Uso:
    python -m rag_leis.responder "sua pergunta"
    python -m rag_leis.responder --modo completa "sua pergunta"   com reranker
"""

import argparse

from rag_leis.citacoes import citacoes_fora_dos_trechos
from rag_leis.dados import artigos_por_id
from rag_leis.generate import generate
from rag_leis.retrieve import MODOS, montar_pipeline


def responder(pergunta: str, modo: str = "rapida") -> dict:
    """Devolve a pergunta, os artigos recuperados, a resposta e as citações sem fonte."""
    artigos = artigos_por_id()
    ids = montar_pipeline(MODOS[modo])(pergunta)
    encontrados = [artigos[i] for i in ids]
    resposta = generate(pergunta, encontrados)
    return {
        "pergunta": pergunta,
        "artigos": encontrados,
        "resposta": resposta,
        "citacoes_fora_dos_trechos": citacoes_fora_dos_trechos(resposta, ids),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("pergunta")
    parser.add_argument("--modo", choices=list(MODOS), default="rapida")
    args = parser.parse_args()
    saida = responder(args.pergunta, args.modo)
    print("Artigos recuperados:")
    for posicao, artigo in enumerate(saida["artigos"], start=1):
        print(f"  {posicao}. {artigo['lei']}, art. {artigo['artigo']}")
    print(f"\nResposta:\n{saida['resposta']}")
    if saida["citacoes_fora_dos_trechos"]:
        fora = ", ".join(saida["citacoes_fora_dos_trechos"])
        print(f"\nAtenção: a resposta cita artigos que o modelo não recebeu: {fora}")


if __name__ == "__main__":
    main()
