"""Corta o texto limpo de cada lei em artigos e grava o corpus.jsonl."""

import json
import re
from pathlib import Path

from rag_leis.ingest import LEIS, Lei, baixar, limpar

CORPUS = Path("data/processed/corpus.jsonl")

# "Art. 1º", "Art. 10.", "Art. 55-A." e o erro de digitação "Art. 5 7." da LGPD.
_INICIO_ARTIGO = re.compile(r"Art\.\s*(\d[\d ]*)[ºo°]?\s*(?:-\s*([A-Z])\b)?")
_TITULO = re.compile(r"T[ÍI]TULO\s+[IVXLC]+(?:-[A-Z])?\b\s*(.*)")
_CAPITULO = re.compile(r"CAP[ÍI]TULO\s+[IVXLC]+(?:-[A-Z])?\b\s*(.*)")
_SECAO = re.compile(
    r"(?:Subse[çc][ãa]o|Se[çc][ãa]o)\s+[IVXLC]+(?:-[A-Z])?\b\s*(.*)", re.IGNORECASE
)
_FECHO = re.compile(r"Bras[íi]lia\s*,\s*\d")
# "(Redação dada pela Lei nº ...)", "(Vide Lei nº ...)" e semelhantes.
_ANOTACAO = re.compile(
    r"\s*\((?:Reda|Inclu|Vide|Vig|Regulament|Revogad|Promulga)[^)]*\)"
)


def _numero_artigo(linha: str) -> tuple[int, str] | None:
    achado = _INICIO_ARTIGO.match(linha)
    if achado is None:
        return None
    return int(achado.group(1).replace(" ", "")), achado.group(2) or ""


def _segue(anterior: tuple[int, str], novo: tuple[int, str]) -> bool:
    """Um artigo novo é o seguinte na numeração ou o mesmo número com letra maior.

    Qualquer outro "Art." em começo de linha é texto citado de outra lei
    (por exemplo, os arts. 337-E a 337-P do Código Penal dentro do art. 178
    da Lei 14.133) e fica dentro do artigo atual.
    """
    if novo[0] == anterior[0] + 1:
        return True
    return novo[0] == anterior[0] and novo[1] > anterior[1]


def _nome(texto: str) -> str:
    return _ANOTACAO.sub("", texto).strip(' "“”‘’')


def cortar(texto: str, lei: Lei) -> list[dict]:
    """Devolve um registro por artigo, com o título e o capítulo em que ele está."""
    linhas = texto.split("\n")
    registros: list[dict] = []
    atual: dict | None = None
    numero = (0, "")
    titulo = capitulo = ""
    # Título e capítulo só valem a partir do próximo artigo da própria lei.
    pendentes: list[str] = []
    novo_titulo, novo_capitulo = titulo, capitulo

    i = 0
    while i < len(linhas):
        linha = linhas[i]
        i += 1

        if atual is not None and _FECHO.match(linha):
            break

        candidato = _numero_artigo(linha)
        if candidato is not None and _segue(numero, candidato):
            numero = candidato
            titulo, capitulo = novo_titulo, novo_capitulo
            pendentes = []
            sufixo = f"-{numero[1]}" if numero[1] else ""
            atual = {
                "id": f"{lei.sigla}-art-{numero[0]}{sufixo}",
                "lei": lei.nome,
                "artigo": f"{numero[0]}{sufixo}",
                "titulo": titulo,
                "capitulo": capitulo,
                "texto": linha,
            }
            registros.append(atual)
            continue

        cabecalho = (
            _TITULO.fullmatch(linha)
            or _CAPITULO.fullmatch(linha)
            or _SECAO.fullmatch(linha)
        )
        if cabecalho is not None and candidato is None:
            nome = _nome(cabecalho.group(1))
            consumidas = [linha]
            # Na Lei 14.133 o nome vem na linha de baixo, às vezes depois de uma anotação.
            while not nome and i < len(linhas) and _numero_artigo(linhas[i]) is None:
                nome = _nome(linhas[i])
                consumidas.append(linhas[i])
                i += 1
            if _TITULO.fullmatch(linha):
                novo_titulo, novo_capitulo = nome, ""
            elif _CAPITULO.fullmatch(linha):
                novo_capitulo = nome
            pendentes.extend(consumidas)
            continue

        if atual is None:
            continue
        if candidato is not None and pendentes:
            # Cabeçalhos seguidos de artigo fora da numeração pertencem a texto citado.
            atual["texto"] += "\n" + "\n".join(pendentes)
            pendentes = []
            novo_titulo, novo_capitulo = titulo, capitulo
        atual["texto"] += "\n" + linha

    return registros


def montar_corpus(destino: Path = CORPUS) -> list[dict]:
    registros: list[dict] = []
    for lei in LEIS:
        texto = limpar(baixar(lei).read_bytes())
        registros.extend(cortar(texto, lei))
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as arquivo:
        for registro in registros:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registros


if __name__ == "__main__":
    corpus = montar_corpus()
    print(f"{len(corpus)} artigos gravados em {CORPUS}")
