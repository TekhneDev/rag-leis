# Experimentos de busca (split dev)

Gerada por `python -m rag_leis.experimento --tabela`. Não edite à mão.

## Geral

| Experimento | Configuração | Recall@1 | Recall@3 | Recall@5 | IC 95% do Recall@5 | MRR |
| --- | --- | --- | --- | --- | --- | --- |
| busca_bm25_cabecalho | bm25 com cabeçalho | 0,35 | 0,47 | 0,53 | 0,35 a 0,71 | 0,43 |
| busca_bm25 | bm25 | 0,23 | 0,44 | 0,50 | 0,32 a 0,68 | 0,35 |
| busca_densa_cabecalho | densa com cabeçalho | 0,68 | 0,78 | 0,90 | 0,79 a 0,98 | 0,79 |
| busca_densa_cabecalho_referencia | densa com cabeçalho + artigo citado primeiro | 0,73 | 0,84 | 0,90 | 0,79 a 0,98 | 0,83 |
| busca_densa_cabecalho_reranker_referencia | densa com cabeçalho + reranker nos 20 primeiros + artigo citado primeiro | 0,79 | 0,91 | 0,94 | 0,85 a 1,00 | 0,89 |
| busca_densa | densa | 0,63 | 0,73 | 0,85 | 0,73 a 0,96 | 0,76 |
| busca_densa_referencia | densa + artigo citado primeiro | 0,69 | 0,79 | 0,88 | 0,77 a 0,97 | 0,81 |
| busca_densa_reranker | densa + reranker nos 20 primeiros | 0,65 | 0,90 | 0,90 | 0,79 a 0,97 | 0,80 |
| busca_densa_reranker_referencia | densa + reranker nos 20 primeiros + artigo citado primeiro | 0,73 | 0,93 | 0,93 | 0,84 a 1,00 | 0,86 |
| busca_hibrida_cabecalho | hibrida com cabeçalho | 0,50 | 0,57 | 0,65 | 0,50 a 0,79 | 0,57 |
| busca_hibrida | hibrida | 0,35 | 0,50 | 0,56 | 0,38 a 0,73 | 0,45 |
| busca_hibrida_peso025 | hibrida (pesos 1 / 0.25) | 0,43 | 0,56 | 0,63 | 0,47 a 0,79 | 0,54 |
| busca_hibrida_peso050 | hibrida (pesos 1 / 0.5) | 0,41 | 0,60 | 0,60 | 0,44 a 0,77 | 0,52 |

## Recall@5 por tipo de pergunta

| Experimento | geral | direta | leiga | varios_artigos | termo_exato |
| --- | --- | --- | --- | --- | --- |
| busca_bm25_cabecalho | 0,53 | 0,86 | 0,00 | 0,40 | 0,80 |
| busca_bm25 | 0,50 | 0,86 | 0,00 | 0,40 | 0,60 |
| busca_densa_cabecalho | 0,90 | 1,00 | 0,80 | 0,90 | 0,80 |
| busca_densa_cabecalho_referencia | 0,90 | 1,00 | 0,80 | 0,90 | 0,80 |
| busca_densa_cabecalho_reranker_referencia | 0,94 | 1,00 | 0,90 | 1,00 | 0,80 |
| busca_densa | 0,85 | 1,00 | 0,80 | 0,80 | 0,60 |
| busca_densa_referencia | 0,88 | 1,00 | 0,80 | 0,80 | 0,80 |
| busca_densa_reranker | 0,90 | 1,00 | 0,90 | 0,90 | 0,60 |
| busca_densa_reranker_referencia | 0,93 | 1,00 | 0,90 | 0,90 | 0,80 |
| busca_hibrida_cabecalho | 0,65 | 1,00 | 0,30 | 0,40 | 0,60 |
| busca_hibrida | 0,56 | 0,93 | 0,20 | 0,40 | 0,40 |
| busca_hibrida_peso025 | 0,63 | 0,93 | 0,40 | 0,50 | 0,40 |
| busca_hibrida_peso050 | 0,60 | 0,93 | 0,30 | 0,50 | 0,40 |

## MRR por tipo de pergunta

| Experimento | geral | direta | leiga | varios_artigos | termo_exato |
| --- | --- | --- | --- | --- | --- |
| busca_bm25_cabecalho | 0,43 | 0,76 | 0,00 | 0,40 | 0,44 |
| busca_bm25 | 0,35 | 0,65 | 0,00 | 0,40 | 0,21 |
| busca_densa_cabecalho | 0,79 | 1,00 | 0,60 | 0,85 | 0,50 |
| busca_densa_cabecalho_referencia | 0,83 | 1,00 | 0,60 | 0,85 | 0,80 |
| busca_densa_cabecalho_reranker_referencia | 0,89 | 1,00 | 0,78 | 0,90 | 0,80 |
| busca_densa | 0,76 | 0,95 | 0,53 | 1,00 | 0,45 |
| busca_densa_referencia | 0,81 | 0,95 | 0,53 | 1,00 | 0,80 |
| busca_densa_reranker | 0,80 | 0,95 | 0,73 | 0,90 | 0,40 |
| busca_densa_reranker_referencia | 0,86 | 0,95 | 0,73 | 0,90 | 0,80 |
| busca_hibrida_cabecalho | 0,57 | 0,91 | 0,17 | 0,40 | 0,60 |
| busca_hibrida | 0,45 | 0,76 | 0,12 | 0,40 | 0,24 |
| busca_hibrida_peso025 | 0,54 | 0,86 | 0,22 | 0,60 | 0,25 |
| busca_hibrida_peso050 | 0,52 | 0,86 | 0,18 | 0,47 | 0,27 |
