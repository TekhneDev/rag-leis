import json

import pytest

from rag_leis.experimento import ler_config, medir_busca


def test_ler_config_preenche_padroes(tmp_path) -> None:
    caminho = tmp_path / "busca_x.json"
    caminho.write_text(json.dumps({"busca": "bm25"}), encoding="utf-8")
    config = ler_config(caminho)
    assert config == {
        "busca": "bm25",
        "k": 5,
        "profundidade": 50,
        "rrf_c": 60,
        "split": "dev",
        "nome": "busca_x",
    }


def test_ler_config_recusa_busca_desconhecida(tmp_path) -> None:
    caminho = tmp_path / "x.json"
    caminho.write_text(json.dumps({"busca": "magica"}), encoding="utf-8")
    with pytest.raises(ValueError):
        ler_config(caminho)


def test_medir_busca_ignora_fora_do_escopo() -> None:
    gold = [
        {
            "id": "q1",
            "tipo": "direta",
            "artigos_esperados": ["a"],
            "artigos_aceitos": [],
        },
        {
            "id": "q2",
            "tipo": "fora_do_escopo",
            "artigos_esperados": [],
            "artigos_aceitos": [],
        },
    ]
    linhas = medir_busca(gold, {"q1": ["b", "a"], "q2": ["c"]})
    assert len(linhas) == 1
    assert linhas[0]["recall@1"] == 0
    assert linhas[0]["recall@3"] == 1
    assert linhas[0]["mrr"] == 0.5
