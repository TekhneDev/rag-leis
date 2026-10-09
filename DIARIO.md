# Diário do projeto

Registro do que foi feito em cada fase, em ordem, com os comandos, as decisões e os problemas encontrados. Tudo aconteceu em 9 de outubro de 2026. O código e os arquivos foram escritos pelo Claude Code a pedido de Carla Braga, que conferiu o corpus e tomou as decisões de projeto. O plano que este diário segue está em [Roadmap RAG jurídico com avaliação](Roadmap%20RAG%20jur%C3%ADdico%20com%20avalia%C3%A7%C3%A3o.md).

## Situação atual

| Fase | Situação | O que falta |
| --- | --- | --- |
| 0. Ambiente | Concluída | Nada |
| 1. Corpus | Concluída | Nada |
| 2. Conjunto ouro | Redigido e revisado por LLM | Validação humana das 75 perguntas |
| 3. Baseline | Concluída | Nada |
| 4. Avaliação | Métricas de busca prontas | Juiz confiável e rotulagem humana de 30 respostas |
| 5. Experimentos | Não iniciada | Tudo |
| 6. Entrega | Não iniciada | Tudo |

Pendências que dependem de uma pessoa:

1. Validar as 75 perguntas em `results/validacao_gold.md`.
2. Rotular 30 respostas em `results/baseline/rotular.md`, preenchendo `results/baseline/rotulos.csv`.

Pendência em andamento quando este diário foi escrito: o download do modelo `gemma3:12b`, para substituir o juiz que falhou (ver fase 4).

## Máquina e versões

- Linux no WSL2, 12 núcleos, 15 GB de RAM, placa de vídeo com 2 GB (pequena demais para os modelos; tudo roda em CPU).
- Python 3.14.4. Fora do ambiente virtual o comando é `python3`; dentro dele, `python`.
- Bibliotecas: torch 2.14.1 (só CPU), sentence-transformers 6.1.0, faiss-cpu 1.15.1, numpy 2.5.3, requests 2.34.2, beautifulsoup4 4.15.0, lxml 6.1.3, ruff 0.16.10, black 26.10.0, pytest 9.1.1.
- Ollama 0.40.2.

O que foi instalado fora da pasta do projeto:

| O quê | Onde | Tamanho |
| --- | --- | --- |
| Ollama | `~/.local/ollama`, com atalho em `~/.local/bin/ollama` | 1,4 GB compactado |
| Modelo `gemma3:4b` | `~/.ollama/models` | 3,4 GB |
| Modelo `gemma3:12b` | `~/.ollama/models` | 8 GB, em download |
| Modelo de embedding `bge-m3` | `~/.cache/huggingface` | 2,2 GB |

O Ollama foi instalado sem `sudo`, descompactando o pacote oficial na pasta do usuário. Por isso ele não sobe sozinho: é preciso rodar `ollama serve` num terminal antes de usar o sistema.

## Fase 0: ambiente

Objetivo: deixar a pasta organizada antes de qualquer código.

```bash
git init
python3 -m venv .venv
mkdir -p data/raw data/processed data/gold src/rag_leis experiments results tests
pip install -e ".[dev]"
ruff check .
black --check .
pytest
```

Arquivos criados: `.gitignore`, `pyproject.toml`, `src/rag_leis/__init__.py`, `tests/test_smoke.py`, `README.md`.

Ajustes em relação ao roteiro original:

- `*.egg-info/` entrou no `.gitignore`, porque a instalação gera essa pasta dentro de `src/`.
- As pastas vazias receberam um arquivo `.gitkeep`, porque o Git não guarda pasta vazia. Eles foram removidos conforme as pastas ganharam conteúdo.
- O repositório `TekhneDev/rag-leis` já existia no GitHub, vazio. O primeiro push foi feito nele.

## Fase 1: corpus

Objetivo: transformar três leis do site do Planalto em `data/processed/corpus.jsonl`, um registro por artigo.

```bash
python -m rag_leis.chunk     # baixa as páginas se preciso, limpa, corta e grava o corpus
```

### Passos

1. **Baixar** (`ingest.py`). As páginas vão para `data/raw/`, que fica fora do Git. São salvos os bytes originais, sem decodificar. O pedido leva um `User-Agent` de navegador.
2. **Limpar** (`ingest.py`). O HTML é decodificado como UTF-8 e, se falhar, como Windows-1252 (as três páginas vieram em Windows-1252). São removidos os trechos riscados (`<strike>`, `<s>`, `<del>` e estilo `line-through`), que são o texto revogado. O resultado é um parágrafo por linha.
3. **Cortar** (`chunk.py`). Um artigo começa numa linha iniciada por "Art. N". O título e o capítulo correntes são gravados em cada artigo.
4. **Conferir**. Testes automáticos e leitura humana de 20 artigos sorteados.

### Resultado

| Lei | Registros | Último artigo |
| --- | --- | --- |
| Lei 13.709/2018 (LGPD) | 80 | 65 |
| Lei 8.078/1990 (CDC) | 130 | 119 |
| Lei 14.133/2021 (licitações) | 196 | 194 |

Total: 406 registros. Há mais registros do que artigos numerados porque artigos incluídos depois ganham letra (55-A, 54-B).

### Problemas encontrados e como foram resolvidos

- **A Lei 14.133 não tem página "compilado".** O endereço dá erro 404. Foi usada a página principal, que traz o texto antigo riscado; ela tinha 21 trechos riscados, todos removidos.
- **Artigos de outra lei dentro de um artigo.** O art. 178 da Lei 14.133 transcreve os arts. 337-E a 337-P do Código Penal, sem aspas. A regra adotada: só é artigo novo o que segue a numeração (o número seguinte, ou o mesmo número com letra maior). Qualquer outro "Art." fica dentro do artigo atual.
- **Erro de digitação na fonte.** A LGPD traz "Art. 5 7." com um espaço. O id ficou certo (`lgpd-art-57`); o texto foi mantido como na fonte.
- **Formatos diferentes de cabeçalho.** Na LGPD e no CDC, "CAPÍTULO I" e o nome vêm na mesma linha; na Lei 14.133, em linhas separadas, às vezes com uma anotação no meio. O cortador trata os dois casos.
- **Assinaturas e rodapé.** O corte termina na linha "Brasília, [data]". Na Lei 14.133, depois dela vêm as partes vetadas promulgadas, que já estão no corpo da lei.
- **Texto restaurado.** O art. 191 da Lei 14.133 aparece riscado e, logo depois, sem risco, porque a medida provisória que o alterava perdeu a vigência. A cópia sem risco é a que vale e foi mantida.
- **Palavra "Vigência" solta.** O Planalto põe um link de navegação no fim de alguns dispositivos. Descoberto na fase 2, ao ler os artigos; removido na limpeza. Trinta artigos mudaram e só essa palavra saiu.

### Decisões que diferem do roadmap

- O campo `artigo` é texto (`"18"`, `"55-A"`), e não número, para que 55 e 55-A não colidam.
- Há um campo `titulo` a mais, porque no CDC e na Lei 14.133 a numeração dos capítulos recomeça a cada título.
- As anotações "(Redação dada pela Lei nº ...)" e "(Incluído pela ...)" ficaram no texto.
- Os 11 artigos que são só "(VETADO)" ou "(Revogado)" ficaram, para a numeração fechar.

### Conferência

- Automática: numeração sem buraco nas três leis, nenhum id repetido, nenhuma assinatura dentro de artigo, nenhum trecho riscado sobrando, nenhuma linha da lei fora de um artigo.
- Automática na amostra: os 20 artigos sorteados aparecem inteiros e contíguos no HTML original.
- Manual: Carla conferiu os 20 artigos contra o original e não registrou divergências. O registro está em `results/conferencia_fase1.md`.

## Fase 2: conjunto ouro

Objetivo: escrever o gabarito antes de existir qualquer busca.

### Passos

1. Leitura de cerca de 70 artigos do corpus, escolhidos para cobrir as três leis.
2. Redação de 75 perguntas, cada uma com a resposta esperada e o artigo que a contém.
3. Divisão em `dev` e `test`, alternando dentro de cada tipo.
4. Revisão das respostas contra o texto dos artigos.
5. Cruzamento de cada pergunta com os artigos correlatos.

### Resultado

| Tipo | Perguntas | Artigos esperados por pergunta |
| --- | --- | --- |
| `direta` | 27 | 1 |
| `leiga` | 19 | 1 |
| `varios_artigos` | 10 | 2 |
| `termo_exato` | 10 | 1 |
| `fora_do_escopo` | 9 | 0 |

São 39 perguntas em `dev` e 36 em `test`. As referências se dividem em 25 para a LGPD, 26 para o CDC e 25 para a Lei 14.133.

### Campo `artigos_aceitos`

Em algumas perguntas, mais de um artigo responde. Para a métrica não acusar erro falso, cada pergunta foi cruzada com os artigos que citam o esperado, os que ele cita e os que usam os mesmos termos. Cada candidato foi lido, e só entrou o que de fato responde.

- `artigos_esperados`: precisam ser recuperados. O recall é calculado sobre eles.
- `artigos_aceitos`: também respondem, no todo ou em parte. Recuperar um deles não conta como erro, mas não substitui o esperado.

Doze perguntas ganharam artigos aceitos, 17 artigos no total. Os motivos estão em `results/validacao_gold.md`.

### Ressalvas

- As perguntas foram redigidas e revisadas pelo mesmo LLM. A revisão não achou erro de fato, mas não é validação independente. Pela regra 3 do roadmap, cada pergunta precisa ser lida por uma pessoa.
- As respostas sobre dispensa de licitação usam R$ 50.000,00 e R$ 100.000,00, que são os valores do texto da lei. A atualização por decreto não está no corpus.
- Nenhuma pergunta fora do escopo trata de crimes em licitação, porque o art. 178 da Lei 14.133 transcreve artigos do Código Penal e a pergunta teria resposta no corpus.
- A pergunta sobre o Marco Civil da Internet (q075) é a mais difícil das fora do escopo: o art. 60 da LGPD cita essa lei, mas não responde à pergunta.

## Fase 3: baseline

Objetivo: a versão mais simples que responde uma pergunta de ponta a ponta, para servir de piso.

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev]"
ollama serve                      # em outro terminal
ollama pull gemma3:4b
python -m rag_leis.index          # gera o índice
python -m rag_leis.responder "O que é cláusula abusiva em contrato de consumo?"
python -m rag_leis.baseline       # roda as 75 perguntas
```

### Escolhas

| Peça | Escolha | Motivo |
| --- | --- | --- |
| Embedding | `BAAI/bge-m3` em CPU | Ponto de partida sugerido no roadmap |
| Banco vetorial | FAISS, busca exata por cosseno | Para 406 artigos não é preciso índice aproximado |
| Recuperação | Densa, 5 artigos por pergunta | O mais simples |
| Geração | `gemma3:4b` no Ollama, temperatura zero, semente fixa | Carla pediu um modelo local, gratuito e bom para aprender |

O código chama o Ollama por HTTP, com a biblioteca `requests`, sem biblioteca intermediária. Assim o pedido e a resposta ficam visíveis em `generate.py`.

O prompt manda o modelo usar só os trechos, citar a lei e o artigo, e responder exatamente "Não encontrei na base." quando os trechos não respondem.

### Decisões que ficam como experimento para a fase 5

- O embedding usa só o texto do artigo, sem o nome da lei nem o capítulo.
- Artigos com mais de 6.000 caracteres são cortados no prompt. Isso afeta os arts. 6º e 75 da Lei 14.133.

### Resultado

- Geração do índice: cerca de 10 minutos, incluído o download do modelo de embedding.
- Uma pergunta de ponta a ponta: de 30 segundos a 1 minuto e meio.
- As 75 perguntas: cerca de 30 minutos. Nenhuma resposta vazia. Saídas em `results/baseline/saidas.jsonl`.

## Fase 4: avaliação

Objetivo: medir a busca e a geração separadamente.

```bash
python -m rag_leis.evaluate                  # busca e abstenção, split dev
python -m rag_leis.evaluate --juiz           # inclui fidelidade e correção
python -m rag_leis.evaluate --sondar         # testa o juiz com respostas falsas
python -m rag_leis.evaluate --rotular        # gera a amostra para rotulagem humana
python -m rag_leis.evaluate --concordancia   # compara os rótulos humanos com o juiz
```

### Métricas

| Métrica | Metade | Como é calculada |
| --- | --- | --- |
| Recall@1, @3, @5 | Busca | Fração dos artigos esperados entre os k primeiros |
| MRR | Busca | Média de 1 dividido pela posição do primeiro artigo esperado |
| Acerto@5 | Busca | Se veio algum artigo esperado ou aceito |
| Abstenção correta | Geração | Nas perguntas fora do escopo, se o sistema disse que não encontrou |
| Correção | Geração | Juiz LLM compara com a resposta esperada |
| Fidelidade | Geração | Juiz LLM confere se cada afirmação está nos trechos |

Cada número sai com a média, o intervalo de 95% por bootstrap (2.000 reamostragens, semente fixa) e a quantidade de perguntas, no geral e por tipo.

O padrão é medir só o `dev`. O `test` exige `--split test` e deve ser usado uma única vez, no fim do projeto. Ele ainda não foi medido.

### Decisões

- O Ragas não foi usado. Com um modelo local pequeno ele é frágil e seus prompts padrão são em inglês. Os dois prompts do juiz estão em português, em `evaluate.py`.
- O juiz inicial foi o mesmo `gemma3:4b` que gera as respostas, por já estar instalado. O modelo do juiz é trocável pela variável `RAG_LEIS_JUIZ`.

### Resultado da busca no `dev`

| Tipo | Perguntas | Recall@1 | Recall@5 | MRR |
| --- | --- | --- | --- | --- |
| Geral | 34 | 0,63 | 0,85 [0,74 a 0,96] | 0,76 |
| Direta | 14 | 0,93 | 1,00 | 0,95 |
| Linguagem leiga | 10 | 0,40 | 0,80 | 0,53 |
| Vários artigos | 5 | 0,50 | 0,80 | 1,00 |
| Termo exato | 5 | 0,40 | 0,60 | 0,45 |

Com 5 ou 10 perguntas por tipo, os intervalos são muito largos. A diferença entre tipos é indício, não prova.

### Resultado da geração no `dev`

- Abstenção correta: 5 de 5 nas perguntas fora do escopo.
- Abstenção indevida: 8 das 34 perguntas com resposta no corpus, 6 delas de linguagem leiga. Na maioria, o artigo certo estava entre os trechos recuperados. É o problema mais claro do baseline.
- Correção, segundo o juiz: 0,65 [0,47 a 0,79]. Ainda não validada contra rótulos humanos.
- Fidelidade, segundo o juiz: 1,00 em 26 respostas. Esse número não vale, pelo motivo abaixo.

### O juiz falhou na sonda

O valor de 100% pareceu bom demais. O juiz recebeu quatro respostas sobre os mesmos trechos do CDC, três delas falsas de propósito:

| Resposta | O juiz deveria | O juiz |
| --- | --- | --- |
| Apoiada no art. 51 | Aprovar | Aprovou |
| Com prazo inventado ("45 dias no Procon") | Reprovar | Aprovou |
| Que contradiz o artigo ("as cláusulas são válidas") | Reprovar | Aprovou |
| Verdadeira, mas de artigo que não foi recuperado | Reprovar | Reprovou |

No caso do prazo, o juiz afirmou que os 45 dias estavam no art. 51. O resultado está em `results/baseline/sonda_juiz.json`.

Decisão de Carla: trocar para um juiz local maior, `gemma3:12b`, e rodar a sonda nele antes de confiar. Se ele também falhar, as alternativas são um juiz por API ou a rotulagem humana.

### Validação humana do juiz

O critério do roadmap é o juiz concordar com uma pessoa em pelo menos 80% de 30 respostas. A amostra de 30 respostas do `dev` está em `results/baseline/rotular.md`. Em 7 delas o sistema disse que não encontrou; nessas, a coluna `fiel` já vem com `-`, porque não há afirmação a conferir.

## Testes

O projeto tem 35 testes, em `tests/`:

| Arquivo | O que confere |
| --- | --- |
| `test_smoke.py` | O pacote instala e importa |
| `test_ingest.py` | Remoção de texto riscado, codificação, espaços |
| `test_chunk.py` | Corte por artigo, letras, artigos citados, títulos e capítulos |
| `test_corpus.py` | Ids únicos, numeração sem buraco, nada de assinatura, nenhuma linha de fora |
| `test_gold.py` | Campos, artigos existentes no corpus, tamanho e divisão |
| `test_generate.py` | Montagem do prompt e corte de artigo longo |
| `test_evaluate.py` | Recall, MRR, acerto, abstenção, bootstrap |

```bash
pytest
ruff check .
black --check .
```

## Commits

| Commit | Conteúdo |
| --- | --- |
| `1392952` | Estrutura inicial do projeto |
| `516ccf3` | README e roadmap |
| `32625d4` | Ingestão das leis e corpus por artigo (fase 1) |
| `8ffe375` | Remoção dos links de "Vigência" do texto dos artigos |
| `eb92ad0` | Conjunto ouro com 75 perguntas (fase 2) |
| `313f2f8` | Registro da conferência manual do corpus; fase 1 concluída |
| `728bf64` | Registro da revisão do conjunto ouro feita por LLM |
| `4a93061` | Correção de dois ids citados errado na nota de revisão |
| `3bb22b5` | Artigos correlatos aceitos no conjunto ouro |
| `9a30ea7` | Baseline: busca densa e geração com LLM local (fase 3) |
| `69ff6f6` | Saídas do baseline nas 75 perguntas; fase 3 concluída |
| `5c990b6` | Avaliação: métricas de busca, abstenção e juiz LLM (fase 4) |
| `cdab1f7` | Métricas do baseline no `dev` e a sonda do juiz |

## Erros meus durante o trabalho

- Na nota de revisão do conjunto ouro, citei dois ids errados (q061 e q067 no lugar de q057 e q063). Corrigido no commit seguinte.
- Um teste meu acusou parágrafo repetido no art. 174 da Lei 14.133. Era falso alarme: "§ 3º-A" é um parágrafo distinto de "§ 3º". O teste foi corrigido.
- Ao regenerar `results/conferencia_fase1.md` depois da remoção da palavra "Vigência", o arquivo voltou com as caixas desmarcadas. Elas foram remarcadas depois que Carla confirmou a conferência.
