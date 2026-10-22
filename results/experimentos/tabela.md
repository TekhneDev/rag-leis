# Experimentos de busca (split dev)

Gerada por `python -m rag_leis.experimento --tabela`. Não edite à mão.

## Geral

| Experimento | Busca | Recall@1 | Recall@3 | Recall@5 | IC 95% do Recall@5 | MRR |
| --- | --- | --- | --- | --- | --- | --- |
| busca_bm25 | bm25 | 0,23 | 0,44 | 0,50 | 0,32 a 0,68 | 0,35 |
| busca_densa | densa | 0,63 | 0,73 | 0,85 | 0,73 a 0,96 | 0,76 |
| busca_hibrida | hibrida | 0,35 | 0,50 | 0,56 | 0,38 a 0,73 | 0,45 |

## Recall@5 por tipo de pergunta

| Experimento | geral | direta | leiga | varios_artigos | termo_exato |
| --- | --- | --- | --- | --- | --- |
| busca_bm25 | 0,50 | 0,86 | 0,00 | 0,40 | 0,60 |
| busca_densa | 0,85 | 1,00 | 0,80 | 0,80 | 0,60 |
| busca_hibrida | 0,56 | 0,93 | 0,20 | 0,40 | 0,40 |

## MRR por tipo de pergunta

| Experimento | geral | direta | leiga | varios_artigos | termo_exato |
| --- | --- | --- | --- | --- | --- |
| busca_bm25 | 0,35 | 0,65 | 0,00 | 0,40 | 0,21 |
| busca_densa | 0,76 | 0,95 | 0,53 | 1,00 | 0,45 |
| busca_hibrida | 0,45 | 0,76 | 0,12 | 0,40 | 0,24 |
