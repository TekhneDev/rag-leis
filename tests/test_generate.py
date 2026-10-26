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


class _RespostaFalsa:
    def __init__(self, status: int = 200, linhas: list[bytes] = (), corpo=None):
        self.status_code, self._linhas, self._corpo = status, linhas, corpo

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return self._corpo

    def iter_lines(self):
        return iter(self._linhas)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def test_conversar_manda_temperatura_zero_e_limpa_a_resposta(monkeypatch) -> None:
    import requests

    from rag_leis import generate

    enviados = {}

    def post(url, json, **_):
        enviados.update(json)
        return _RespostaFalsa(corpo={"message": {"content": "  Sim.\n"}})

    monkeypatch.setattr(requests, "post", post)
    assert generate.conversar("sistema", "usuario", formato_json=True) == "Sim."
    assert enviados["options"]["temperature"] == 0
    assert enviados["format"] == "json"
    assert enviados["stream"] is False


def test_gerar_em_partes_junta_os_pedacos_ate_o_fim(monkeypatch) -> None:
    import requests

    from rag_leis import generate

    linhas = [
        b'{"message": {"content": "Sim, "}, "done": false}',
        b"",
        b'{"message": {"content": "pode."}, "done": true}',
        b'{"message": {"content": "ignorado"}}',
    ]
    monkeypatch.setattr(requests, "post", lambda *a, **k: _RespostaFalsa(linhas=linhas))
    assert "".join(generate.gerar_em_partes("?", ARTIGOS)) == "Sim, pode."


def test_erros_do_ollama_dizem_o_que_fazer(monkeypatch) -> None:
    import pytest
    import requests

    from rag_leis import generate

    monkeypatch.setattr(requests, "post", lambda *a, **k: _RespostaFalsa(404))
    with pytest.raises(RuntimeError, match="ollama pull"):
        generate.conversar("s", "u", modelo="nao-existe")

    def sem_servidor(*a, **k):
        raise requests.ConnectionError

    monkeypatch.setattr(requests, "post", sem_servidor)
    with pytest.raises(RuntimeError, match="ollama serve"):
        generate.conversar("s", "u")
