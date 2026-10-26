import json

import pytest

from rag_leis.experimento import ler_config, medir_busca, rotulo
from rag_leis.retrieve import PADRAO, com_referencia


def test_ler_config_preenche_padroes(tmp_path) -> None:
    caminho = tmp_path / "busca_x.json"
    caminho.write_text(json.dumps({"busca": "bm25"}), encoding="utf-8")
    config = ler_config(caminho)
    assert config["nome"] == "busca_x"
    assert config["k"] == 5
    assert config["referencia"] is False
    assert config["pesos"] == [1.0, 1.0]


def test_rotulo_descreve_as_variacoes() -> None:
    config = PADRAO | {"busca": "hibrida", "pesos": [1, 0.25], "referencia": True}
    assert rotulo(config) == "hibrida (pesos 1 / 0.25) + artigo citado primeiro"
    assert rotulo(PADRAO | {"busca": "densa"}) == "densa"


def test_referencia_poe_o_citado_na_frente(monkeypatch) -> None:
    from rag_leis import retrieve

    corpus = [
        {"id": i, "texto": ""} for i in ("cdc-art-49", "cdc-art-18", "lgpd-art-7")
    ]
    monkeypatch.setattr(retrieve, "carregar_corpus", lambda: corpus)
    buscar = com_referencia(
        lambda pergunta, n: ["cdc-art-18", "cdc-art-49", "lgpd-art-7"][:n]
    )
    assert buscar("O que diz o art. 49 do CDC?", 2) == ["cdc-art-49", "cdc-art-18"]
    assert buscar("Posso devolver?", 2) == ["cdc-art-18", "cdc-art-49"]


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


def test_modos_do_app_sao_configuracoes_medidas() -> None:
    """Cada modo do app e do responder tem um experimento com a mesma configuração."""
    from rag_leis.dados import EXPERIMENTOS
    from rag_leis.retrieve import MODOS

    medidas = {
        "rapida": "busca_densa_cabecalho_referencia",
        "completa": "busca_densa_cabecalho_reranker_referencia",
    }
    for modo, nome in medidas.items():
        config = ler_config(EXPERIMENTOS / f"{nome}.json")
        assert config | {"nome": None} == MODOS[modo] | {"nome": None}, modo


def test_ler_config_recusa_chave_com_erro_de_digitacao(tmp_path) -> None:
    caminho = tmp_path / "x.json"
    caminho.write_text(
        json.dumps({"busca": "densa", "reranquer": "x"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="reranquer"):
        ler_config(caminho)


def test_todos_os_experimentos_do_repositorio_sao_validos() -> None:
    from rag_leis.dados import EXPERIMENTOS

    caminhos = sorted(EXPERIMENTOS.glob("*.json"))
    assert caminhos
    for caminho in caminhos:
        ler_config(caminho)


def test_baseline_com_modo_roda_so_o_dev_e_retoma(monkeypatch, tmp_path) -> None:
    from rag_leis import baseline

    gold = [
        {"id": "q1", "tipo": "direta", "split": "dev", "pergunta": "A?"},
        {"id": "q2", "tipo": "direta", "split": "test", "pergunta": "B?"},
        {"id": "q3", "tipo": "leiga", "split": "dev", "pergunta": "C?"},
    ]
    monkeypatch.setattr(
        baseline, "ler_jsonl", lambda c: gold if c == baseline.GOLD else [{"id": "q1"}]
    )
    monkeypatch.setattr(
        baseline,
        "_busca_do_modo",
        lambda modo: lambda p: ([{"id": "cdc-art-49"}], {"modo": modo}),
    )
    monkeypatch.setattr(baseline, "generate", lambda p, a: "Sim.")
    saidas = tmp_path / "saidas.jsonl"
    saidas.write_text('{"id": "q1"}\n', encoding="utf-8")
    assert baseline.rodar(saidas, modo="completa", split="dev") == 1
    gravada = json.loads(saidas.read_text(encoding="utf-8").splitlines()[-1])
    assert gravada["id"] == "q3"
    assert gravada["modo"] == "completa"
    assert gravada["recuperados"] == ["cdc-art-49"]
