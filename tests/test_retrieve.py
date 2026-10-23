import pytest

from rag_leis.retrieve import BuscadorBM25, artigos_citados, fundir_rrf, tokenizar


def test_tokenizar_tira_acento_e_stopwords() -> None:
    assert tokenizar("A revogação do consentimento") == ["revogacao", "consentimento"]


def test_tokenizar_mantem_artigo_com_letra() -> None:
    assert tokenizar("art. 42-A da Lei 8.078") == ["art", "42-a", "lei", "8", "078"]


def test_bm25_traz_o_artigo_com_as_palavras_da_pergunta() -> None:
    corpus = [
        {"id": "a", "texto": "O consumidor pode desistir do contrato em sete dias."},
        {"id": "b", "texto": "A licitação será processada e julgada."},
        {"id": "c", "texto": "O titular dos dados pessoais tem direito de acesso."},
    ]
    resultado = BuscadorBM25(corpus).buscar("direito de acesso aos dados", k=2)
    assert resultado[0]["id"] == "c"
    assert len(resultado) == 2


def test_rrf_premia_quem_aparece_nas_duas_listas() -> None:
    fundido = [artigo for artigo, _ in fundir_rrf([["a", "b", "c"], ["c", "d", "a"]])]
    assert fundido[:2] == ["a", "c"]
    assert set(fundido) == {"a", "b", "c", "d"}


def test_rrf_pontuacao_do_primeiro_lugar() -> None:
    assert fundir_rrf([["a"]], c=60) == [("a", pytest.approx(1 / 61))]


def test_rrf_com_peso_favorece_a_primeira_lista() -> None:
    fundido = fundir_rrf([["a", "b"], ["b", "a"]], pesos=[1.0, 0.25])
    assert [artigo for artigo, _ in fundido] == ["a", "b"]


IDS = {"lgpd-art-7", "cdc-art-7", "cdc-art-42-A", "licitacoes-art-75"}


def test_artigos_citados_respeita_a_lei_nomeada() -> None:
    assert artigos_citados("O que diz o art. 75 da Lei 14.133?", IDS) == [
        "licitacoes-art-75"
    ]
    assert artigos_citados("O art. 42-A da Lei 8.078/1990", IDS) == ["cdc-art-42-A"]


def test_artigos_citados_sem_lei_vale_para_todas() -> None:
    assert artigos_citados("O que diz o artigo 7º?", IDS) == ["lgpd-art-7", "cdc-art-7"]


def test_artigos_citados_ignora_pergunta_sem_numero() -> None:
    assert artigos_citados("Comprei e me arrependi, posso devolver?", IDS) == []
