"""Confere o conjunto ouro contra o corpus."""

import json
from collections import Counter
from pathlib import Path

import pytest

from rag_leis.chunk import CORPUS

GOLD = Path("data/gold/gold.jsonl")
TIPOS = {"direta", "leiga", "varios_artigos", "termo_exato", "fora_do_escopo"}

pytestmark = pytest.mark.skipif(
    not GOLD.exists(), reason="conjunto ouro ainda não escrito"
)


def _ler(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo]


@pytest.fixture(scope="module")
def gold() -> list[dict]:
    return _ler(GOLD)


def test_campos_e_valores(gold: list[dict]) -> None:
    for item in gold:
        assert set(item) == {
            "id",
            "tipo",
            "pergunta",
            "artigos_esperados",
            "artigos_aceitos",
            "resposta_esperada",
            "split",
        }
        assert item["tipo"] in TIPOS, item["id"]
        assert item["split"] in {"dev", "test"}, item["id"]
        assert item["pergunta"].strip() and item["resposta_esperada"].strip(), item[
            "id"
        ]


def test_ids_e_perguntas_unicos(gold: list[dict]) -> None:
    assert len({item["id"] for item in gold}) == len(gold)
    assert len({item["pergunta"] for item in gold}) == len(gold)


def test_artigos_esperados_existem_no_corpus(gold: list[dict]) -> None:
    ids = {registro["id"] for registro in _ler(CORPUS)}
    for item in gold:
        assert set(item["artigos_esperados"]) <= ids, item["id"]


def test_artigos_aceitos_existem_e_nao_repetem_os_esperados(gold: list[dict]) -> None:
    ids = {registro["id"] for registro in _ler(CORPUS)}
    for item in gold:
        aceitos = set(item["artigos_aceitos"])
        assert aceitos <= ids, item["id"]
        assert not aceitos & set(item["artigos_esperados"]), item["id"]
        if item["tipo"] == "fora_do_escopo":
            assert not aceitos, item["id"]


def test_quantidade_de_artigos_combina_com_o_tipo(gold: list[dict]) -> None:
    for item in gold:
        quantidade = len(item["artigos_esperados"])
        if item["tipo"] == "fora_do_escopo":
            assert quantidade == 0, item["id"]
        elif item["tipo"] == "varios_artigos":
            assert quantidade >= 2, item["id"]
        else:
            assert quantidade == 1, item["id"]


def test_tamanho_e_divisao(gold: list[dict]) -> None:
    assert 60 <= len(gold) <= 80
    for tipo in TIPOS:
        splits = Counter(item["split"] for item in gold if item["tipo"] == tipo)
        assert abs(splits["dev"] - splits["test"]) <= 1, tipo
