"""Teste de fumaça: garante que o pacote instala e importa."""

import rag_leis


def test_package_imports() -> None:
    assert rag_leis is not None
