from rag_leis.ingest import limpar


def _pagina(corpo: str) -> bytes:
    return f"<html><body>{corpo}</body></html>".encode("windows-1252")


def test_remove_texto_riscado() -> None:
    html = _pagina(
        "<p>Art. 1º Texto vigente.</p>"
        "<p><strike>Art. 2º Texto revogado.</strike></p>"
        '<p><span style="text-decoration: line-through">§ 1º Também revogado.</span></p>'
    )
    assert limpar(html) == "Art. 1º Texto vigente."


def test_decodifica_windows_1252_e_utf8() -> None:
    assert limpar(_pagina("<p>Seção I</p>")) == "Seção I"
    assert limpar("<html><body><p>Seção I</p></body></html>".encode()) == "Seção I"


def test_um_paragrafo_por_linha_sem_espacos_repetidos() -> None:
    html = _pagina("<p>Art. 1º  Primeira<br>parte.</p><p>§ 1º&nbsp;Segunda.</p>")
    assert limpar(html) == "Art. 1º Primeira parte.\n§ 1º Segunda."


def test_descarta_marcacao_de_vigencia_encerrada() -> None:
    assert (
        limpar(_pagina("<p>Art. 1º Vale.</p><p>Vigência encerrada</p>"))
        == "Art. 1º Vale."
    )
