# rag-leis

Sistema de perguntas e respostas (RAG) sobre três leis brasileiras, com uma tabela de experimentos que mede o que faz o sistema acertar mais.

> Este projeto é um estudo e não substitui orientação jurídica.

## Status

Em construção. O corpus está gerado (406 artigos das três leis); ainda não há busca nem geração.

| Fase | Entregável | Situação |
| --- | --- | --- |
| 0. Ambiente | Repositório com estrutura de pastas, lint e teste | Concluída |
| 1. Corpus | `corpus.jsonl`, um registro por artigo | Gerado; falta a conferência manual de 20 artigos |
| 2. Conjunto ouro | `gold.jsonl` com 60 a 80 perguntas | A fazer |
| 3. Baseline | Pipeline de ponta a ponta com busca densa | A fazer |
| 4. Avaliação | `evaluate.py` e números do baseline | A fazer |
| 5. Experimentos | Tabela de resultados e análise de erros | A fazer |
| 6. Entrega | App e demo | A fazer |

O plano completo, com conceitos, métricas e armadilhas, está em [Roadmap RAG jurídico com avaliação](Roadmap%20RAG%20jur%C3%ADdico%20com%20avalia%C3%A7%C3%A3o.md).

## Corpus

Texto publicado no site do Planalto, baixado em 9 de outubro de 2026, sem os trechos revogados:

| Lei | Registros | Último artigo |
| --- | --- | --- |
| Lei 13.709/2018 (LGPD) | 80 | 65 |
| Lei 8.078/1990 (Código de Defesa do Consumidor) | 130 | 119 |
| Lei 14.133/2021 (licitações e contratos administrativos) | 196 | 194 |

Há mais registros do que o número do último artigo porque artigos incluídos depois ganham letra (por exemplo, art. 55-A). Cada linha de `data/processed/corpus.jsonl` tem `id`, `lei`, `artigo`, `titulo`, `capitulo` e `texto`.

Para gerar o corpus de novo (baixa as páginas para `data/raw/` se ainda não estiverem lá):

```bash
python -m rag_leis.chunk
```

A amostra para conferência manual está em `results/conferencia_fase1.md`.

## Estrutura

```text
rag-leis/
  data/raw/          # HTML original das leis (fora do Git)
  data/processed/    # corpus.jsonl
  data/gold/         # gold.jsonl
  src/rag_leis/      # código do pacote
  experiments/       # um arquivo de configuração por experimento
  results/           # saídas e tabela final
  tests/
  pyproject.toml
```

## Como rodar

Requer Python 3.10 ou mais recente.

```bash
git clone https://github.com/TekhneDev/rag-leis.git
cd rag-leis
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Conferência do ambiente:

```bash
ruff check .
black --check .
pytest
```

Chaves de API, quando forem necessárias, ficam num arquivo `.env`, que está no `.gitignore`.
