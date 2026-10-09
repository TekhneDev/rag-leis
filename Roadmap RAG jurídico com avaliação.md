# Roadmap: RAG jurídico com avaliação

Oct 8, 2026 · @Carla Braga

O projeto entrega um sistema de perguntas e respostas sobre três leis brasileiras e, principalmente, uma tabela de experimentos que prova com números o que faz esse sistema acertar mais. São 7 fases, cerca de 6 semanas a 5 ou 6 horas por semana (estimativa, ajuste ao seu ritmo).

## Conceitos do zero

RAG transforma a prova sem consulta de um modelo de linguagem em prova com consulta. Sozinho, o modelo (LLM) responde só com o que absorveu no treinamento e pode inventar com confiança, o que se chama alucinação. Com RAG (Retrieval-Augmented Generation), o sistema primeiro busca os trechos certos nos seus documentos e só depois o modelo responde, citando de onde tirou.

O sistema tem seis peças, sempre nesta ordem:

1. **Ingestão.** Converter os documentos (HTML, PDF) em texto limpo. É como digitalizar um arquivo de papel: se a digitalização sai borrada, nada depois conserta.
2. **Chunking.** Cortar o texto em pedaços menores, os chunks. Você entrega ao modelo algumas páginas, nunca o livro inteiro. Em lei, o corte natural é o artigo.
3. **Embedding.** Transformar cada chunk em um vetor, uma lista de números que funciona como coordenada de significado num mapa. Textos sobre o mesmo assunto ficam vizinhos, mesmo com palavras diferentes.
4. **Banco vetorial.** Guardar esses vetores num lugar que responde rápido à pergunta "quais são os vizinhos mais próximos deste ponto?".
5. **Recuperação.** Transformar a pergunta do usuário em vetor e trazer os k chunks mais próximos. Pode ser por significado (busca densa), por palavra exata (BM25) ou pelas duas juntas (híbrida).
6. **Geração.** Entregar pergunta e trechos ao LLM, com a instrução de responder só com base neles, citar o artigo e dizer "não encontrei" quando os trechos não respondem.

A avaliação é a sétima peça e a mais importante para uma vaga de cientista de dados. Um RAG erra em dois lugares diferentes: a busca não trouxe o trecho certo, ou trouxe e o modelo respondeu mal. Cada falha tem conserto próprio, então cada uma precisa de métrica própria.

## Roadmap

Cada fase depende da anterior, e a ordem mais importante é escrever o conjunto ouro (fase 2) antes de montar qualquer busca (fase 3). É a mesma lógica de separar o conjunto de teste antes de treinar um modelo.

| Fase | Semana | O que você faz | Entregável | Pronto quando |
| --- | --- | --- | --- | --- |
| 0. Ambiente | 1 | Repositório, ambiente virtual, lint | Repo no GitHub com estrutura de pastas | `ruff` e `pytest` rodam sem erro |
| 1. Corpus | 1 | Baixar as 3 leis e cortar por artigo | `corpus.jsonl`, um registro por artigo | 20 artigos sorteados conferidos à mão contra o original |
| 2. Conjunto ouro | 2 | Escrever perguntas com resposta e artigo esperado | `gold.jsonl` com 60 a 80 perguntas | Cada pergunta aponta para um artigo que existe no corpus |
| 3. Baseline | 3 | Embedding, banco vetorial, busca densa, geração | Pipeline que responde uma pergunta de ponta a ponta | Roda nas 60 a 80 perguntas e salva as saídas |
| 4. Avaliação | 4 | Métricas de recuperação e de geração, validação do juiz | Script `evaluate.py` e números do baseline | Juiz LLM concorda com você em pelo menos 80% de 30 respostas |
| 5. Experimentos | 5 | Variar uma peça por vez | Tabela de resultados e análise de erros | Cada linha da tabela é reproduzível por um comando |
| 6. Entrega | 6 | App, README, texto de divulgação | Repositório público e demo | Alguém de fora clona e roda seguindo só o README |

O limiar de 80% de concordância na fase 4 é uma regra prática minha, e não um padrão da literatura.

## Fases 0 e 1: ambiente e corpus

Comece pela estrutura do repositório, porque ela obriga a lógica a morar em módulos `.py` testáveis e deixa os notebooks só para explorar.

```text
rag-leis/
  data/raw/          # HTML original das leis (não versionar se for grande)
  data/processed/    # corpus.jsonl
  data/gold/         # gold.jsonl
  src/rag_leis/
    ingest.py        # baixar e limpar
    chunk.py         # cortar por artigo
    index.py         # embeddings e banco vetorial
    retrieve.py      # busca densa, BM25, híbrida
    generate.py      # prompt e chamada ao LLM
    evaluate.py      # métricas
  experiments/       # um arquivo de configuração por experimento
  results/           # saídas e tabela final
  tests/
  app.py
  pyproject.toml
  README.md
```

Passos da fase 0:

1. Criar o repositório e o ambiente virtual (`uv` ou `venv`), com as versões fixadas no `pyproject.toml`.
2. Configurar `ruff` e `black`, e um teste vazio no `pytest` para o pipeline de CI já nascer funcionando.
3. Guardar chaves de API num arquivo `.env` que está no `.gitignore`. Chave publicada no GitHub é o acidente mais comum de portfólio.

Passos da fase 1:

1. Baixar do site do Planalto a Lei 14.133/2021 (licitações), a Lei 13.709/2018 (LGPD) e a Lei 8.078/1990 (Código de Defesa do Consumidor), sempre na versão "compilada".
2. Limpar o HTML. O Planalto mantém o texto revogado na página, riscado. Se você não remover as tags de texto riscado, o sistema vai citar regra que não vale mais.
3. Conferir a codificação. Essas páginas costumam vir em Latin-1, e ler como UTF-8 troca os acentos por símbolos.
4. Cortar por artigo com uma expressão regular sobre "Art. N". Cada registro guarda lei, número do artigo, capítulo e texto completo com parágrafos e incisos.
5. Sortear 20 artigos e comparar com o original, linha a linha.

Um registro do `corpus.jsonl` fica assim:

```json
{"id": "lgpd-art-18", "lei": "Lei 13.709/2018", "artigo": 18, "capitulo": "Dos direitos do titular", "texto": "Art. 18. O titular dos dados pessoais tem direito a obter do controlador..."}
```

## Fase 2: conjunto ouro

O conjunto ouro é o gabarito do projeto: 60 a 80 perguntas, cada uma com a resposta esperada e o artigo que a contém. Ele faz o papel do conjunto de teste em ML clássico, e sem ele qualquer melhoria vira opinião.

Misture cinco tipos de pergunta, porque cada tipo quebra o sistema de um jeito diferente:

| Tipo | Quantas | Exemplo | O que testa |
| --- | --- | --- | --- |
| Direta | 25 a 30 | Quais direitos o titular pode exigir do controlador? (LGPD, art. 18) | O caso básico |
| Linguagem leiga | 15 a 20 | Comprei pela internet e me arrependi, posso devolver? (CDC, art. 49) | Busca por significado, sem as palavras da lei |
| Vários artigos | 8 a 10 | Em que hipóteses posso tratar dados sensíveis sem consentimento? (LGPD, arts. 7 e 11) | Recuperar mais de um trecho |
| Termo exato | 6 a 10 | O que diz o art. 75 da Lei 14.133? | Busca por palavra-chave |
| Fora do escopo | 8 a 10 | Qual o prazo para entrar com ação trabalhista? | Se o sistema admite que não sabe |

Um registro do `gold.jsonl`:

```json
{"id": "q017", "tipo": "leiga", "pergunta": "Comprei pela internet e me arrependi, posso devolver?", "artigos_esperados": ["cdc-art-49"], "resposta_esperada": "Sim, em até 7 dias a contar da assinatura ou do recebimento, para compras fora do estabelecimento comercial.", "split": "dev"}
```

Três regras para o gabarito valer:

1. Escreva as perguntas antes de construir a busca. Se você escrever depois, vai escolher sem perceber as perguntas que o sistema acerta.
2. Divida em `dev` e `test`, metade para cada. Você ajusta o sistema olhando o `dev` e reporta o resultado final no `test`, uma única vez. Sem isso, cinco rodadas de ajuste viram overfitting no gabarito.
3. Pode pedir a um LLM sugestões de pergunta, mas leia o artigo e valide cada uma. Pergunta gerada e não conferida costuma repetir as palavras do texto, o que deixa a busca fácil demais.

## Fases 3 e 4: baseline e avaliação

O baseline é a versão mais simples que funciona de ponta a ponta, e existe para dar um piso de comparação. Resista a melhorar qualquer coisa antes de medir.

Passos da fase 3:

1. Gerar o embedding de cada artigo com um modelo multilíngue aberto via `sentence-transformers`. O `bge-m3` é um ponto de partida comum.
2. Guardar os vetores num banco local (Chroma ou FAISS). Para algumas centenas de artigos, nada além disso é necessário.
3. Escrever `retrieve(pergunta, k=5)`, que devolve os 5 artigos mais próximos.
4. Escrever `generate(pergunta, artigos)`, com um prompt que manda responder só com base nos trechos, citar lei e artigo, e responder "não encontrei na base" quando for o caso.
5. Rodar o conjunto ouro inteiro e salvar, para cada pergunta, os artigos recuperados e a resposta gerada.

Na fase 4 você mede as duas metades separadamente:

| Métrica | Metade | Pergunta que responde | Como calcular |
| --- | --- | --- | --- |
| Recall@k | Recuperação | O artigo certo apareceu entre os k trazidos? | Código puro, comparando ids com `artigos_esperados` |
| MRR | Recuperação | Quão perto do topo ele apareceu? | Código puro: média de 1 dividido pela posição do primeiro acerto |
| Fidelidade (faithfulness) | Geração | Cada afirmação da resposta está apoiada nos trechos? | LLM como juiz, por exemplo com o Ragas |
| Correção factual | Geração | A resposta bate com a resposta esperada? | LLM como juiz |
| Taxa de abstenção correta | Geração | Nas perguntas fora do escopo, o sistema disse que não sabe? | Código puro sobre as perguntas do tipo "fora do escopo" |

Como você cortou por artigo e anotou o artigo esperado, as métricas de recuperação saem sem LLM nenhum, baratas e determinísticas. Essa é a maior vantagem de ter escolhido legislação.

Dois cuidados com o juiz LLM:

1. **Valide o juiz.** Rotule você mesma 30 respostas como fiéis ou não, compare com o juiz e reporte a concordância. Uma régua que ninguém conferiu não mede nada.
2. **Fixe a versão do Ragas.** A [documentação](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) lista Faithfulness, Factual Correctness, Context Recall e Response Relevancy, mas a biblioteca já teve migrações que quebram código (há um guia da v0.3 para a v0.4). Siga o tutorial da versão instalada, e use o guia de adaptação de métricas para outros idiomas, já que os prompts padrão são em inglês.

Sobre a escolha do embedding: um [benchmark de 2026 para português](https://www.catalyzex.com/paper/beyond-multilingual-averages-mteb-pt-a) concluiu que rankings multilíngues não preveem bem o desempenho em português e que nenhum modelo vence em todas as tarefas. Por isso o modelo de embedding entra como variável de experimento na fase 5, medido no seu próprio conjunto ouro.

## Fases 5 e 6: experimentos e entrega

Na fase 5 você muda uma peça por vez e mantém o resto igual ao baseline, como num experimento de laboratório. Mudar duas coisas juntas impede saber qual delas causou o ganho.

| Experimento | Opções comparadas | Hipótese a testar |
| --- | --- | --- |
| Chunking | Por artigo, contra blocos fixos de 500 caracteres | Cortar por artigo aumenta o recall porque preserva a unidade de sentido |
| Tipo de busca | Densa, BM25, híbrida | A híbrida ganha nas perguntas de termo exato sem perder nas leigas |
| Reranker | Sem, contra com | O reranker melhora o MRR mais do que o recall |
| Valor de k | 3, 5, 10 | Mais trechos aumentam o recall, mas podem reduzir a fidelidade |
| Modelo de embedding | 2 ou 3 modelos multilíngues | O melhor no ranking geral pode não ser o melhor em texto jurídico em português |

Passos da fase 5:

1. Criar um arquivo de configuração por experimento em `experiments/`, e um único comando que recebe a configuração e grava as métricas em `results/`.
2. Rodar tudo no `dev`. Reportar os resultados por tipo de pergunta, e não só a média geral, porque é aí que as diferenças aparecem.
3. Fazer a análise de erros: ler cada falha da melhor configuração e classificá-la em falha de busca, falha de geração, erro do gabarito ou pergunta ambígua.
4. Rodar a melhor configuração e o baseline no `test`, uma vez, e registrar os dois números.

Com 30 a 40 perguntas por split, diferenças pequenas são ruído. Reporte um intervalo de confiança por bootstrap e diga no README que a amostra é pequena; isso conta a favor em entrevista.

Passos da fase 6:

1. Montar um app em Streamlit com campo de pergunta, resposta e os artigos usados ao lado, com link para o texto.
2. Escrever o README nesta ordem: o resultado em uma frase com número, a tabela de experimentos, três erros reais comentados, limitações, como rodar.
3. Colocar um aviso no app e no README de que o sistema é um estudo e não substitui orientação jurídica.
4. Publicar e escrever um texto curto contando o que a tabela mostrou, de preferência um achado que contrariou sua hipótese.

Uma segunda versão pode ampliar o corpus para editais reais do PNCP (Portal Nacional de Contratações Públicas), que tem consulta pública por API. Editais são PDFs longos e irregulares, então só vale a pena depois que o pipeline de avaliação estiver pronto.

## Armadilhas

Cinco erros invalidam o resultado sem dar nenhuma mensagem de erro, então confira cada um antes de publicar.

- **Vazamento do gabarito.** Ajustar prompt e parâmetros olhando as mesmas perguntas em que você reporta o resultado. A divisão `dev` e `test` existe para isso.
- **Texto revogado no corpus.** O sistema cita com segurança um artigo que não vale mais. Confira a limpeza do texto riscado na fase 1.
- **Média que esconde o problema.** Um recall geral alto pode conviver com recall baixo nas perguntas leigas, que são as que um usuário real faria.
- **Juiz não validado.** Fidelidade de 0,90 medida por um juiz que concorda com você em 60% dos casos não significa nada.
- **Resultados não reproduzíveis.** Chamadas a LLM variam entre execuções. Use temperatura zero, salve todas as saídas em disco e fixe as versões das bibliotecas e do modelo.

## Fontes

- [Ragas: lista de métricas disponíveis](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [Okamura, Alcoforado e Costa: MTEB-PT, benchmark de embeddings para português (2026)](https://www.catalyzex.com/paper/beyond-multilingual-averages-mteb-pt-a)

Os números de artigos das leis citados nos exemplos vêm do meu conhecimento e não foram conferidos nesta sessão; valide cada um ao montar o corpus. A página de manuais da API do PNCP não abriu na consulta, então confirme o acesso antes de planejar a segunda versão.
