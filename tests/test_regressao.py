"""Teste de regressão da busca: o BM25 tem de reproduzir o resultado gravado no dev.

Roda no CI porque o BM25 só precisa do corpus e do gabarito, sem baixar modelo.
Se uma mudança em tokenizar, no corpus ou no executor mudar um único artigo
recuperado, o teste falha e a tabela de experimentos precisa ser refeita.
"""

import json

import pytest

from rag_leis.dados import CORPUS, EXPERIMENTOS, GOLD, RESULTADOS, ler_jsonl
from rag_leis.experimento import ler_config, medir_busca
from rag_leis.retrieve import montar_pipeline

GRAVADO = RESULTADOS / "experimentos" / "busca_bm25_dev.json"

pytestmark = pytest.mark.skipif(
    not (CORPUS.exists() and GOLD.exists() and GRAVADO.exists()),
    reason="corpus, gabarito ou resultado gravado ausente",
)


def test_bm25_reproduz_o_resultado_gravado_no_dev() -> None:
    gravado = json.loads(GRAVADO.read_text(encoding="utf-8"))
    config = ler_config(EXPERIMENTOS / "busca_bm25.json")
    gold = [item for item in ler_jsonl(GOLD) if item["split"] == "dev"]
    buscar = montar_pipeline(config)
    recuperados = {item["id"]: buscar(item["pergunta"]) for item in gold}
    assert recuperados == gravado["recuperados"]
    linhas = medir_busca(gold, recuperados)
    recall = sum(linha["recall@5"] for linha in linhas) / len(linhas)
    assert round(recall, 3) == gravado["metricas"]["geral"]["recall@5"]["media"]
