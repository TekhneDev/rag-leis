# rag-leis

Sistema de perguntas e respostas (RAG) sobre três leis brasileiras, com uma tabela de experimentos que mede o que faz o sistema acertar mais.

> Este projeto é um estudo e não substitui orientação jurídica.

## Status

Em construção. O sistema já responde perguntas de ponta a ponta com busca densa e um LLM local; ainda não há métricas.

| Fase | Entregável | Situação |
| --- | --- | --- |
| 0. Ambiente | Repositório com estrutura de pastas, lint e teste | Concluída |
| 1. Corpus | `corpus.jsonl`, um registro por artigo | Concluída |
| 2. Conjunto ouro | `gold.jsonl` com 60 a 80 perguntas | Redigido; falta a validação manual das perguntas |
| 3. Baseline | Pipeline de ponta a ponta com busca densa | Concluída |
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

Uma amostra de 20 artigos sorteados foi conferida à mão contra o original; o registro está em `results/conferencia_fase1.md`.

## Conjunto ouro

`data/gold/gold.jsonl` tem 75 perguntas, cada uma com a resposta esperada e os artigos do corpus que a contêm. Foi escrito antes de existir qualquer busca.

Cada pergunta tem dois campos de artigos:

- `artigos_esperados`: os artigos que precisam ser recuperados para a resposta estar completa. É sobre eles que o recall é calculado.
- `artigos_aceitos`: artigos correlatos que também respondem, no todo ou em parte (12 perguntas têm algum). Recuperar um deles não conta como erro, mas não substitui o esperado.

| Tipo | Perguntas | O que testa |
| --- | --- | --- |
| `direta` | 27 | O caso básico |
| `leiga` | 19 | Busca por significado, sem as palavras da lei |
| `varios_artigos` | 10 | Recuperar mais de um trecho |
| `termo_exato` | 10 | Busca por palavra-chave |
| `fora_do_escopo` | 9 | Se o sistema admite que não sabe |

A divisão é de 39 perguntas em `dev` e 36 em `test`, metade de cada tipo em cada parte. O sistema é ajustado olhando só o `dev`; o `test` é usado uma única vez, no resultado final.

As perguntas foram redigidas por um LLM a partir do texto do corpus e ainda precisam de validação humana, uma a uma. A lista para isso está em `results/validacao_gold.md`.

## Estrutura

```text
rag-leis/
  data/raw/          # HTML original das leis (fora do Git)
  data/processed/    # corpus.jsonl
  data/gold/         # gold.jsonl
  data/index/        # vetores dos artigos (fora do Git, gerado por comando)
  src/rag_leis/
    ingest.py        # baixar e limpar
    chunk.py         # cortar por artigo
    index.py         # embeddings e índice vetorial
    retrieve.py      # busca densa
    generate.py      # prompt e chamada ao LLM
    responder.py     # uma pergunta de ponta a ponta
    baseline.py      # conjunto ouro inteiro
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
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev]"
```

A primeira linha do `pip` instala o PyTorch só para CPU, que é bem menor. Quem tem placa de vídeo com bastante memória pode pular essa linha.

Conferência do ambiente:

```bash
ruff check .
black --check .
pytest
```

## Baseline

O baseline é a versão mais simples que funciona, para servir de piso de comparação:

| Peça | Escolha |
| --- | --- |
| Chunking | Um chunk por artigo, só o texto do artigo |
| Embedding | `BAAI/bge-m3`, em CPU |
| Banco vetorial | FAISS, busca exata por cosseno |
| Recuperação | Densa, 5 artigos por pergunta |
| Geração | `gemma3:4b` rodando localmente no Ollama, temperatura zero |

O LLM é local e gratuito. Instale o [Ollama](https://ollama.com/download), deixe o servidor no ar e baixe o modelo (3,4 GB):

```bash
ollama serve            # em um terminal separado, se o servidor ainda não estiver no ar
ollama pull gemma3:4b
```

Gere o índice uma vez (baixa o modelo de embedding, cerca de 2 GB, e leva alguns minutos em CPU):

```bash
python -m rag_leis.index
```

Faça uma pergunta:

```bash
python -m rag_leis.responder "O que é cláusula abusiva em contrato de consumo?"
```

A saída mostra os 5 artigos recuperados, com a pontuação de similaridade, e a resposta com a lei e o artigo citados. Em CPU, cada resposta leva de um a dois minutos.

Rode o conjunto ouro inteiro e salve as saídas em `results/baseline/saidas.jsonl`:

```bash
python -m rag_leis.baseline
```

O comando pode ser interrompido e retomado: ele pula as perguntas que já têm saída.

Para usar outro modelo do Ollama, defina a variável `RAG_LEIS_LLM` antes de rodar. O projeto não usa chave de API; se um dia usar, ela fica num arquivo `.env`, que está no `.gitignore`.
