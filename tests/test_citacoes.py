from rag_leis.citacoes import (
    artigos_citados,
    citacoes_da_resposta,
    citacoes_fora_dos_trechos,
)

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


def test_citacao_entre_parenteses_com_paragrafo_e_letra() -> None:
    resposta = (
        "Sim (Lei 8.078/1990, art. 49). Veja também (Lei 8.078/1990, art. 37, § 1°) "
        "e (Lei 8.078/1990, art. 54-A)."
    )
    assert citacoes_da_resposta(resposta) == [
        "cdc-art-49",
        "cdc-art-37",
        "cdc-art-54-A",
    ]


def test_citacao_com_a_lei_depois_e_lista_de_artigos() -> None:
    assert citacoes_da_resposta(
        "Art. 51, inciso VI, da Lei 8.078/1990: inversão do ônus."
    ) == ["cdc-art-51"]
    assert citacoes_da_resposta("Nos artigos 75 e 85 da Lei 14.133/2021.") == [
        "licitacoes-art-75",
        "licitacoes-art-85",
    ]
    assert citacoes_da_resposta("O art. 51 do Código de Defesa do Consumidor.") == [
        "cdc-art-51"
    ]


def test_artigo_sem_lei_e_lei_fora_do_corpus_nao_contam() -> None:
    assert citacoes_da_resposta("Conforme o art. 75, a licitação é dispensável.") == []
    assert citacoes_da_resposta("Revogam-se os arts. 89 a 108 da Lei nº 8.666") == []


def test_citacao_fora_dos_trechos_aponta_invencao() -> None:
    resposta = "Pode revogar (Lei 13.709/2018, art. 5º, § 5º)."
    assert citacoes_fora_dos_trechos(resposta, ["lgpd-art-8"]) == ["lgpd-art-5"]
    assert citacoes_fora_dos_trechos(resposta, ["lgpd-art-5"]) == []
