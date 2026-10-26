from rag_leis.dados import escrever_linha, ler_jsonl


def test_escreve_e_le_jsonl_com_acento(tmp_path) -> None:
    caminho = tmp_path / "x.jsonl"
    registros = [{"id": "q1", "pergunta": "Licitação?"}, {"id": "q2", "n": 2}]
    with caminho.open("w", encoding="utf-8") as arquivo:
        for registro in registros:
            escrever_linha(arquivo, registro)
    assert ler_jsonl(caminho) == registros
    assert "Licitação" in caminho.read_text(encoding="utf-8")
