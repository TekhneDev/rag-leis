import pytest

from rag_leis.retrieve import BuscadorBM25, fundir_rrf, tokenizar


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


def test_texto_indexado_com_cabecalho_nomeia_a_lei() -> None:
    from rag_leis.index import texto_indexado

    registro = {
        "lei": "Lei 8.078/1990",
        "artigo": "49",
        "titulo": "Dos Direitos do Consumidor",
        "capitulo": "",
        "texto": "Art. 49. O consumidor pode desistir do contrato...",
    }
    assert texto_indexado(registro) == registro["texto"]
    com = texto_indexado(registro, cabecalho=True)
    assert com.startswith(
        "Lei 8.078/1990 (Código de Defesa do Consumidor, CDC), art. 49 · Dos Direitos"
    )
    assert com.endswith(registro["texto"])
