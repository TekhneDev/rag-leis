import pytest

from rag_leis.dados import RAIZ

testing = pytest.importorskip("streamlit.testing.v1")


def test_as_duas_paginas_abrem_sem_erro() -> None:
    app = testing.AppTest.from_file(str(RAIZ / "app.py"), default_timeout=60).run()
    assert not app.exception
    app.switch_page("paginas/avaliacao.py").run()
    assert not app.exception
    assert app.subheader[0].value == "Resumo: busca completa contra o baseline"
    assert len(app.metric) == 8
