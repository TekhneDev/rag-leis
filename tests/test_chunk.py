from rag_leis.chunk import cortar
from rag_leis.ingest import Lei

LEI = Lei("teste", "Lei 1/2000", "http://exemplo")


def _cortar(*linhas: str) -> list[dict]:
    return cortar("\n".join(linhas), LEI)


def test_um_registro_por_artigo() -> None:
    registros = _cortar(
        "LEI Nº 1",
        "Art. 1º Primeiro.",
        "§ 1º Parágrafo.",
        "Art. 2° Segundo.",
        "Brasília, 1º de janeiro de 2000",
        "FULANO",
    )
    assert [r["id"] for r in registros] == ["teste-art-1", "teste-art-2"]
    assert registros[0]["texto"] == "Art. 1º Primeiro.\n§ 1º Parágrafo."
    assert registros[1]["texto"] == "Art. 2° Segundo."
    assert registros[0]["lei"] == "Lei 1/2000"


def test_artigo_com_letra_e_numero_com_espaco() -> None:
    registros = _cortar("Art. 1º A.", "Art. 1º-A. B.", "Art. 1º-B. C.", "Art. 2 . D.")
    assert [r["artigo"] for r in registros] == ["1", "1-A", "1-B", "2"]
    registros = _cortar(
        *[f"Art. {n}º X." for n in range(1, 10)], "Art. 1 0. Y.", "Art. 11. Z."
    )
    assert [r["artigo"] for r in registros][-2:] == ["10", "11"]


def test_artigo_citado_de_outra_lei_fica_dentro_do_artigo_atual() -> None:
    registros = _cortar(
        "Art. 1º O Código Penal passa a vigorar com o seguinte artigo:",
        "Art. 337-E. Admitir contratação direta ilegal.",
        "“Art. 2º ......",
        "Art. 2º Segue.",
    )
    assert [r["artigo"] for r in registros] == ["1", "2"]
    assert "Art. 337-E" in registros[0]["texto"]
    assert "“Art. 2º" in registros[0]["texto"]


def test_referencia_no_meio_do_paragrafo_nao_corta() -> None:
    registros = _cortar("Art. 1º Nos termos do art. 5º desta Lei.", "Art. 2º Fim.")
    assert len(registros) == 2


def test_titulo_e_capitulo_na_mesma_linha_ou_na_de_baixo() -> None:
    registros = _cortar(
        "TÍTULO I Dos Direitos",
        "CAPÍTULO I Disposições Gerais (Vide Lei nº 9, de 1999)",
        "Art. 1º A.",
        "CAPÍTULO II",
        "(Redação dada pela Lei nº 8, de 1998)",
        "DO PORTAL (PNCP)",
        "Seção I",
        "Das Regras",
        "Art. 2º B.",
        "TÍTULO II",
        "DAS PENAS",
        "Art. 3º C.",
    )
    assert [(r["titulo"], r["capitulo"]) for r in registros] == [
        ("Dos Direitos", "Disposições Gerais"),
        ("Dos Direitos", "DO PORTAL (PNCP)"),
        ("DAS PENAS", ""),
    ]
    assert registros[0]["texto"] == "Art. 1º A."
    assert registros[1]["texto"] == "Art. 2º B."


def test_capitulo_citado_de_outra_lei_nao_muda_o_capitulo() -> None:
    registros = _cortar(
        "CAPÍTULO I DAS ALTERAÇÕES",
        "Art. 1º O Código passa a vigorar acrescido do seguinte capítulo:",
        "CAPÍTULO II-B",
        "DOS CRIMES",
        "Art. 337-E. Crime.",
        "Art. 2º Segue.",
    )
    assert [r["capitulo"] for r in registros] == ["DAS ALTERAÇÕES", "DAS ALTERAÇÕES"]
    assert "DOS CRIMES" in registros[0]["texto"]
