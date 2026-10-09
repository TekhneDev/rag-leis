"""Baixa as leis do site do Planalto e converte o HTML em texto limpo."""

import re
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup

RAW_DIR = Path("data/raw")

_BASE = "https://www.planalto.gov.br/ccivil_03"
_RISCADO = re.compile(r"line-through", re.IGNORECASE)
_ESPACOS = re.compile(r"[ \t\r\f\v\xa0]+")
# Marcações do Planalto que sobram sozinhas na linha depois que o texto riscado sai.
_ANOTACOES = {"Vigência encerrada"}
# Links de navegação que o Planalto põe no fim do dispositivo e não são texto da lei.
_LINKS_DE_ANOTACAO = {"Vigência"}


@dataclass(frozen=True)
class Lei:
    sigla: str
    nome: str
    url: str

    @property
    def caminho_raw(self) -> Path:
        return RAW_DIR / f"{self.sigla}.html"


LEIS = [
    Lei(
        "lgpd", "Lei 13.709/2018", f"{_BASE}/_ato2015-2018/2018/lei/l13709compilado.htm"
    ),
    Lei("cdc", "Lei 8.078/1990", f"{_BASE}/leis/l8078compilado.htm"),
    # A Lei 14.133 não tem página "compilado": a página principal já traz as alterações.
    Lei("licitacoes", "Lei 14.133/2021", f"{_BASE}/_ato2019-2022/2021/lei/l14133.htm"),
]


def baixar(lei: Lei, forcar: bool = False) -> Path:
    """Salva os bytes originais da página em data/raw/, sem decodificar."""
    destino = lei.caminho_raw
    if destino.exists() and not forcar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    resposta = requests.get(lei.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    resposta.raise_for_status()
    destino.write_bytes(resposta.content)
    return destino


def decodificar(html_bytes: bytes) -> str:
    """As páginas do Planalto variam entre UTF-8 e Windows-1252."""
    try:
        return html_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return html_bytes.decode("windows-1252")


def limpar(html_bytes: bytes) -> str:
    """Devolve o texto vigente da lei, um parágrafo por linha.

    Remove o texto revogado, que o Planalto mantém riscado na página.
    """
    soup = BeautifulSoup(decodificar(html_bytes), "lxml")
    for tag in soup.find_all(["script", "style", "strike", "s", "del"]):
        tag.decompose()
    for tag in soup.find_all(style=_RISCADO):
        tag.decompose()
    for link in soup.find_all("a"):
        if _ESPACOS.sub(" ", link.get_text(" ")).strip(" ()\n") in _LINKS_DE_ANOTACAO:
            link.decompose()
    for quebra in soup.find_all("br"):
        quebra.replace_with(" ")

    linhas = []
    for bloco in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"]):
        linha = _ESPACOS.sub(" ", bloco.get_text(" ").replace("\n", " ")).strip()
        if linha and linha not in _ANOTACOES:
            linhas.append(linha)
    return "\n".join(linhas)


if __name__ == "__main__":
    for lei in LEIS:
        print(f"{lei.sigla}: {baixar(lei)}")
