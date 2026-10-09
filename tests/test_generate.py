from rag_leis.generate import (
    INSTRUCOES,
    MAX_CARACTERES_POR_ARTIGO,
    NAO_ENCONTREI,
    montar_prompt,
)

ARTIGOS = [
    {
        "lei": "Lei 8.078/1990",
        "artigo": "49",
        "texto": "Art. 49. O consumidor pode desistir.",
    },
    {"lei": "Lei 13.709/2018", "artigo": "55-A", "texto": "Art. 55-A. Fica criada."},
]


def test_prompt_traz_lei_artigo_texto_e_pergunta() -> None:
    prompt = montar_prompt("Posso devolver?", ARTIGOS)
    assert "[Lei 8.078/1990, art. 49]\nArt. 49. O consumidor pode desistir." in prompt
    assert "[Lei 13.709/2018, art. 55-A]" in prompt
    assert prompt.endswith("Pergunta: Posso devolver?")


def test_artigo_longo_e_cortado() -> None:
    longo = {
        "lei": "Lei 1",
        "artigo": "6",
        "texto": "x" * (MAX_CARACTERES_POR_ARTIGO + 500),
    }
    prompt = montar_prompt("?", [longo])
    assert "x" * MAX_CARACTERES_POR_ARTIGO + "\n[trecho cortado]" in prompt
    assert "x" * (MAX_CARACTERES_POR_ARTIGO + 1) not in prompt


def test_instrucoes_pedem_abstencao_com_frase_fixa() -> None:
    assert NAO_ENCONTREI in INSTRUCOES
