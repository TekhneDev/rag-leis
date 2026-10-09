"""Confere o corpus gerado. Regenere com `python -m rag_leis.chunk`."""

import json
import re
from collections import Counter

import pytest

from rag_leis.chunk import CORPUS, cortar
from rag_leis.ingest import LEIS, limpar

ULTIMO_ARTIGO = {"Lei 13.709/2018": 65, "Lei 8.078/1990": 119, "Lei 14.133/2021": 194}

pytestmark = pytest.mark.skipif(not CORPUS.exists(), reason="corpus ainda não gerado")


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    with CORPUS.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo]


def test_ids_unicos(corpus: list[dict]) -> None:
    repetidos = [i for i, n in Counter(r["id"] for r in corpus).items() if n > 1]
    assert repetidos == []


def test_campos_preenchidos(corpus: list[dict]) -> None:
    for registro in corpus:
        assert set(registro) == {"id", "lei", "artigo", "titulo", "capitulo", "texto"}
        assert registro["texto"].startswith("Art.")
        assert registro["titulo"] or registro["capitulo"], registro["id"]


def test_numeracao_sem_buraco(corpus: list[dict]) -> None:
    for lei, ultimo in ULTIMO_ARTIGO.items():
        numeros = {int(r["artigo"].split("-")[0]) for r in corpus if r["lei"] == lei}
        assert numeros == set(range(1, ultimo + 1)), lei


def test_sem_assinatura_nem_rodape(corpus: list[dict]) -> None:
    for registro in corpus:
        assert "não substitui o publicado" not in registro["texto"], registro["id"]
        assert not re.search(
            r"^Bras[íi]lia\s*,\s*\d", registro["texto"], re.MULTILINE
        ), registro["id"]


def test_paragrafo_nao_aparece_duas_vezes_no_mesmo_artigo(corpus: list[dict]) -> None:
    """Parágrafo repetido indica redação antiga que não foi removida."""
    for registro in corpus:
        # Só vale para artigos que não citam o texto de outra lei.
        if "“" in registro["texto"] or '"' in registro["texto"]:
            continue
        paragrafos = re.findall(
            r"^§ ?(\d+[ºo°]?(?:-[A-Z])?)", registro["texto"], re.MULTILINE
        )
        assert len(paragrafos) == len(set(paragrafos)), registro["id"]


@pytest.mark.parametrize("lei", LEIS, ids=lambda lei: lei.sigla)
def test_nenhuma_linha_da_lei_fica_de_fora(lei, corpus: list[dict]) -> None:
    """Do art. 1º ao fecho, toda linha é texto de artigo ou cabeçalho de título, capítulo ou seção."""
    if not lei.caminho_raw.exists():
        pytest.skip("HTML original não baixado")
    linhas = limpar(lei.caminho_raw.read_bytes()).split("\n")
    registros = cortar("\n".join(linhas), lei)
    assert registros == [r for r in corpus if r["lei"] == lei.nome]

    inicio = next(i for i, linha in enumerate(linhas) if linha.startswith("Art."))
    fim = next(
        i for i, linha in enumerate(linhas) if re.match(r"Bras[íi]lia\s*,\s*\d", linha)
    )
    em_artigos = Counter(linha for r in registros for linha in r["texto"].split("\n"))
    sobras = [linha for linha in linhas[inicio:fim] if linha not in em_artigos]
    assert all(len(linha) < 150 for linha in sobras)
    assert len(sobras) < 150
