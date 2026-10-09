# rag-leis

Sistema de perguntas e respostas (RAG) sobre três leis brasileiras, com uma tabela de experimentos que mede o que faz o sistema acertar mais.

> Este projeto é um estudo e não substitui orientação jurídica.

## Status

Em construção. A fase 0 (ambiente) está concluída; ainda não há corpus, busca nem geração.

| Fase | Entregável | Situação |
| --- | --- | --- |
| 0. Ambiente | Repositório com estrutura de pastas, lint e teste | Concluída |
| 1. Corpus | `corpus.jsonl`, um registro por artigo | A fazer |
| 2. Conjunto ouro | `gold.jsonl` com 60 a 80 perguntas | A fazer |
| 3. Baseline | Pipeline de ponta a ponta com busca densa | A fazer |
| 4. Avaliação | `evaluate.py` e números do baseline | A fazer |
| 5. Experimentos | Tabela de resultados e análise de erros | A fazer |
| 6. Entrega | App e demo | A fazer |

O plano completo, com conceitos, métricas e armadilhas, está em [Roadmap RAG jurídico com avaliação](Roadmap%20RAG%20jur%C3%ADdico%20com%20avalia%C3%A7%C3%A3o.md).

## Corpus planejado

Versões compiladas publicadas no site do Planalto:

- Lei 14.133/2021 (licitações e contratos administrativos)
- Lei 13.709/2018 (LGPD)
- Lei 8.078/1990 (Código de Defesa do Consumidor)

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
