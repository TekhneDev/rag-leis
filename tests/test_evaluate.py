import pytest

from rag_leis import evaluate
from rag_leis.evaluate import (
    absteve,
    acerto_em_k,
    intervalo_bootstrap,
    medir,
    recall_em_k,
    reciproco_da_posicao,
    resumir,
)

RECUPERADOS = ["a", "b", "c", "d", "e"]


def test_recall_em_k() -> None:
    assert recall_em_k(RECUPERADOS, ["c"], 5) == 1
    assert recall_em_k(RECUPERADOS, ["c"], 1) == 0
    assert recall_em_k(RECUPERADOS, ["a", "z"], 5) == 0.5


def test_reciproco_da_posicao() -> None:
    assert reciproco_da_posicao(RECUPERADOS, ["a"]) == 1
    assert reciproco_da_posicao(RECUPERADOS, ["z", "c"]) == pytest.approx(1 / 3)
    assert reciproco_da_posicao(RECUPERADOS, ["z"]) == 0


def test_acerto_conta_artigo_aceito() -> None:
    assert acerto_em_k(RECUPERADOS, ["z"], ["e"], 5) == 1
    assert acerto_em_k(RECUPERADOS, ["z"], ["e"], 3) == 0
    assert acerto_em_k(RECUPERADOS, ["z"], [], 5) == 0


def test_absteve_reconhece_a_frase_fixa() -> None:
    assert absteve("Não encontrei na base.")
    assert absteve("não encontrei na base")
    assert not absteve("Sim, em até 7 dias (Lei 8.078/1990, art. 49).")


def test_intervalo_bootstrap_contem_a_media_e_e_reproduzivel() -> None:
    valores = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
    baixo, alto = intervalo_bootstrap(valores)
    assert baixo <= sum(valores) / len(valores) <= alto
    assert intervalo_bootstrap(valores) == (baixo, alto)
    assert intervalo_bootstrap([1.0, 1.0]) == (1.0, 1.0)


def test_medir_e_resumir_separam_busca_e_abstencao() -> None:
    gold = [
        {
            "id": "q1",
            "tipo": "direta",
            "artigos_esperados": ["a"],
            "artigos_aceitos": [],
        },
        {
            "id": "q2",
            "tipo": "direta",
            "artigos_esperados": ["z"],
            "artigos_aceitos": ["b"],
        },
        {
            "id": "q3",
            "tipo": "fora_do_escopo",
            "artigos_esperados": [],
            "artigos_aceitos": [],
        },
    ]
    saidas = [
        {"id": "q1", "recuperados": RECUPERADOS, "resposta": "Sim."},
        {"id": "q2", "recuperados": RECUPERADOS, "resposta": "Não encontrei na base."},
        {"id": "q3", "recuperados": RECUPERADOS, "resposta": "Não encontrei na base."},
    ]
    linhas = medir(gold, saidas, {"q1": {"fiel": True, "correta": False}})
    assert (
        linhas[0]["recall@5"] == 1
        and linhas[0]["fiel"] == 1
        and linhas[0]["correta"] == 0
    )
    assert (
        linhas[1]["recall@5"] == 0
        and linhas[1]["acerto@5"] == 1
        and linhas[1]["absteve"] == 1
    )
    assert "recall@5" not in linhas[2] and linhas[2]["abstencao_correta"] == 1
    assert linhas[1]["abstencao_indevida"] == 1 and linhas[0]["abstencao_indevida"] == 0
    assert "abstencao_indevida" not in linhas[2]

    resumo = resumir(linhas)
    assert resumo["geral"]["recall@5"] == {
        "media": 0.5,
        "ic95": resumo["geral"]["recall@5"]["ic95"],
        "n": 2,
    }
    assert resumo["fora_do_escopo"]["abstencao_correta"]["media"] == 1
    assert resumo["direta"]["fiel"]["n"] == 1


def test_cada_juiz_grava_no_seu_arquivo(monkeypatch, tmp_path):
    monkeypatch.setattr(evaluate, "MODELO_JUIZ", "gemma3:4b")
    pequeno = evaluate.arquivo_do_juiz(tmp_path, "julgamentos.jsonl")
    monkeypatch.setattr(evaluate, "MODELO_JUIZ", "gemma3:12b")
    grande = evaluate.arquivo_do_juiz(tmp_path, "julgamentos.jsonl")
    assert pequeno.name == "julgamentos_gemma3-4b.jsonl"
    assert grande.name == "julgamentos_gemma3-12b.jsonl"


def test_metricas_de_busca_de_uma_pergunta() -> None:
    from rag_leis.evaluate import metricas_de_busca

    item = {"artigos_esperados": ["b", "z"], "artigos_aceitos": ["e"]}
    assert metricas_de_busca(RECUPERADOS, item) == {
        "recall@1": 0,
        "recall@3": 0.5,
        "recall@5": 0.5,
        "mrr": 0.5,
        "acerto@5": 1,
    }


def test_metricas_de_citacao() -> None:
    from rag_leis.evaluate import metricas_de_citacao

    assert metricas_de_citacao("Sim (Lei 8.078/1990, art. 49).", ["cdc-art-49"]) == {
        "cita_artigo": 1,
        "citacoes_nos_trechos": 1,
    }
    assert metricas_de_citacao("Sim (Lei 8.078/1990, art. 49).", ["cdc-art-18"]) == {
        "cita_artigo": 1,
        "citacoes_nos_trechos": 0,
    }
    assert metricas_de_citacao("Sim, pode devolver.", ["cdc-art-49"]) == {
        "cita_artigo": 0
    }
