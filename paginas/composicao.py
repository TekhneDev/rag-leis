"""Compõe o texto de um artigo como num código impresso.

Cada linha do corpus é um dispositivo: o caput ("Art. 49."), um parágrafo ("§ 1º",
"Parágrafo único."), um inciso ("I -"), uma alínea ("a)"), um item ("1)") ou a
pena ("Pena -"). Cada um vira um parágrafo HTML com a classe do seu nível, para o
CSS dar o recuo de cada nível. As notas de redação, como "(Redação dada pela Lei nº 13.853, de
2019)", saem em corpo menor, como nos vade mecuns.
"""

import re
from html import escape

# Ordem importa: "Parágrafo único" antes de qualquer outro, inciso antes de alínea.
DISPOSITIVOS = [
    ("caput", re.compile(r"^(Art\. ?\d+[º°o]?(?:-[A-Z])?\.?)\s*(.*)$")),
    (
        "paragrafo",
        re.compile(r"^(Parágrafo único\.?|§ ?\d+[º°o]?(?:-[A-Z])?\.?)\s*(.*)$"),
    ),
    ("inciso", re.compile(r"^([IVXLC]+(?:-[A-Z])?)\s*[-–—]\s*(.*)$")),
    ("alinea", re.compile(r"^([a-z](?:-[A-Z])?\))\s*(.*)$")),
    ("item", re.compile(r"^(\d+\))\s*(.*)$")),
    ("pena", re.compile(r"^(Pena)\s*[-–—]?\s*(.*)$")),
]
NOTA_DE_REDACAO = re.compile(
    r"\((?:Redação dada|Incluíd[oa]|Vide|Revogad[oa]|Vigência|Regulamento|"
    r"Produção de efeitos?|Promulgação|Renumerad[oa]|Acrescid[oa])[^()]*\)"
)


def _com_notas(texto: str) -> str:
    """Escapa o texto e põe as notas de redação em <span class="nota-red">."""
    partes, inicio = [], 0
    for achado in NOTA_DE_REDACAO.finditer(texto):
        partes.append(escape(texto[inicio : achado.start()]))
        partes.append(f'<span class="nota-red">{escape(achado.group())}</span>')
        inicio = achado.end()
    partes.append(escape(texto[inicio:]))
    return "".join(partes)


def classificar(linha: str) -> tuple[str, str, str]:
    """(nível, marcador, resto) de uma linha; nível "solto" se não casar com nada."""
    for nivel, padrao in DISPOSITIVOS:
        achado = padrao.match(linha)
        if achado:
            return nivel, achado.group(1), achado.group(2)
    return "solto", "", linha


def compor(texto: str) -> str:
    """HTML do artigo, um <p> por dispositivo."""
    paragrafos = []
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        nivel, marcador, resto = classificar(linha)
        if nivel in ("inciso", "pena"):
            marcador = f"{marcador} –"
        marca = f'<b class="mk">{escape(marcador)}</b> ' if marcador else ""
        paragrafos.append(f'<p class="{nivel}">{marca}{_com_notas(resto)}</p>')
    return "".join(paragrafos)
