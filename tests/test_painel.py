import json

from rag_leis.painel import (
    EVOLUCAO,
    estado_do_juiz,
    evolucao_da_busca,
    experimentos,
    linhas_de_metrica,
    metricas_da_rodada,
    mudancas,
    numero,
    por_pergunta,
)


def _escrever(caminho, registros) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in registros), "utf-8"
    )


def _cenario(tmp_path):
    gold = tmp_path / "gold.jsonl"
    _escrever(
        gold,
        [
            {
                "id": "q1",
                "tipo": "leiga",
                "split": "dev",
                "pergunta": "Posso devolver?",
                "artigos_esperados": ["cdc-art-49"],
                "artigos_aceitos": [],
            },
            {
                "id": "q2",
                "tipo": "fora_do_escopo",
                "split": "dev",
                "pergunta": "Pena por dirigir bêbado?",
                "artigos_esperados": [],
                "artigos_aceitos": [],
            },
            {
                "id": "q9",
                "tipo": "leiga",
                "split": "test",
                "pergunta": "pergunta do test",
                "artigos_esperados": ["cdc-art-1"],
                "artigos_aceitos": [],
            },
        ],
    )
    respostas = {
        "baseline": {
            "q1": (["cdc-art-2"], "Não encontrei na base."),
            "q2": (["cdc-art-3"], "Não encontrei na base."),
        },
        "completa": {
            "q1": (["cdc-art-49"], "Sete dias (Lei 8.078/1990, art. 26)."),
            "q2": (["cdc-art-3"], "Não encontrei na base."),
        },
    }
    corretas = {"baseline": False, "completa": True}
    for rodada, por_id in respostas.items():
        saidas = [
            {"id": i, "split": "dev", "recuperados": r, "resposta": t}
            for i, (r, t) in por_id.items()
        ]
        # A rodada do baseline tem também o test; a página não pode lê-lo.
        saidas.append({"id": "q9", "split": "test", "recuperados": [], "resposta": "x"})
        _escrever(tmp_path / rodada / "saidas.jsonl", saidas)
        _escrever(
            tmp_path / rodada / "julgamentos_gemma3-12b.jsonl",
            [{"id": "q1", "correta": corretas[rodada]}, {"id": "q9", "correta": True}],
        )
    return gold


def test_por_pergunta_so_le_o_dev(tmp_path) -> None:
    linhas = por_pergunta(tmp_path, _cenario(tmp_path))
    assert [linha["id"] for linha in linhas] == ["q1", "q2"]


def test_por_pergunta_compara_as_rodadas(tmp_path) -> None:
    q1, q2 = por_pergunta(tmp_path, _cenario(tmp_path))
    assert q1["baseline_posicao"] is None and q1["completa_posicao"] == 1
    assert q1["baseline_absteve"] and not q1["completa_absteve"]
    assert q1["completa_fora"] == ["cdc-art-26"]
    assert "baseline_posicao" not in q2


def test_mudancas_ignora_fora_do_escopo(tmp_path) -> None:
    trocas = mudancas(por_pergunta(tmp_path, _cenario(tmp_path)))
    assert trocas["passou_a_correta"] == ["q1"]
    assert trocas["deixou_de_se_abster"] == ["q1"]
    assert trocas["cita_fora_dos_trechos"] == ["q1"]
    assert trocas["deixou_de_ser_correta"] == []


def test_numero_usa_virgula() -> None:
    assert numero(0.736) == "0,74"
    assert numero(1.0) == "1,00"


def test_le_os_resultados_gravados() -> None:
    """A página depende dos arquivos do repositório; um nome trocado quebraria ela."""
    registros = experimentos()
    assert {nome for nome, _ in EVOLUCAO} <= {r["nome"] for r in registros}
    assert len(evolucao_da_busca(registros)) == 3 * len(EVOLUCAO)
    for rodada in ("baseline", "completa"):
        metricas = metricas_da_rodada(rodada)
        tipos = [linha["tipo"] for linha in linhas_de_metrica(metricas, "recall@5")]
        assert tipos[0] == "Geral" and "Fora do escopo" not in tipos
    juiz = estado_do_juiz()
    assert juiz["rotulos_necessarios"] == 30 and juiz["sonda"]
