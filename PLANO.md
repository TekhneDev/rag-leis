# Plano de carreira e de implementação

Oct 22, 2026 · @Carla Braga

Este plano junta duas coisas: o que falta construir no rag-leis e o que cada etapa mostra para quem contrata. O cargo-alvo é cientista de dados com foco em NLP e LLM; o segundo caminho é AI Engineer. O ritmo segue o do [roadmap](Roadmap%20RAG%20jur%C3%ADdico%20com%20avalia%C3%A7%C3%A3o.md), 5 a 6 horas por semana.

A apresentação visual do projeto, com a demo e a parte de carreira, está em https://claude.ai/artifact/Xo7NBBVKz94tU4ZDxnU57G (privada até ser compartilhada).

As recomendações de mercado vêm do conhecimento do Claude até meados de 2026, e não de uma pesquisa de vagas. Antes da etapa 3, conte as ferramentas que se repetem em 15 a 20 vagas reais do cargo-alvo e ajuste a ordem.

## Princípio

Cada ferramenta nova entra no rag-leis como experimento medido, e não como curso concluído. Em entrevista, "testei busca híbrida e ela piorou o recall de 0,85 para 0,56; descobri o porquê" vale mais que "sei usar BM25".

## Etapas

| Etapa | Semanas | O que entra | Entregável | Pronto quando | Situação |
| --- | --- | --- | --- | --- | --- |
| 1. Base de engenharia | 1 | GitHub Actions (ruff, black, pytest) | `.github/workflows/ci.yml` e selo no README | O CI passa no GitHub | Feito; falta ver o primeiro run verde |
| 2. Busca por palavra | 1 | BM25, híbrida com RRF, executor de experimentos | `experiments/*.json`, `results/experimentos/tabela.md` | Cada linha da tabela sai de um comando | Feito |
| 3. Pendências humanas | 1 a 2 | Validar o gabarito e rotular 30 respostas | `validacao_gold.md` marcado, `rotulos.csv` preenchido | Concordância do juiz de pelo menos 80% | A fazer (só Carla pode fazer) |
| 4. Melhorar a busca | 2 | Busca por referência ("art. N da Lei X"), híbrida com peso, reranker | Novas linhas na tabela | Hipóteses abaixo testadas | Feito |
| 5. Melhorar a geração | 1 | Prompt menos rígido e variação de k | Respostas novas julgadas pelo juiz validado | Abstenção indevida medida antes e depois | A fazer; depende da etapa 3 |
| 6. Ferramentas de avaliação | 1 | Ragas ao lado do juiz próprio; MLflow para os experimentos | Comparação de concordância; runs no MLflow | As duas réguas comparadas com os rótulos humanos | A fazer |
| 7. Entrega | 1 a 2 | App em Streamlit, README na ordem do roadmap, texto de divulgação | Demo pública | Alguém de fora roda seguindo só o README | App e README feitos; falta demo pública e texto |
| 8. Produção | 2 a 3 | FastAPI, Docker, API comercial (Claude) contra o modelo local, Langfuse | Endpoint `/perguntar` em container | Custo e latência por pergunta medidos | Depois da entrega |
| 9. Diferenciais | contínuo | pgvector ou Qdrant, agente com uso de ferramentas, nuvem, editais do PNCP | Um item por vez | Cada um com número na tabela | Depois |

Fora do projeto, em paralelo: SQL com um conjunto de dados tabular (uma tarde por semana), e um texto curto no LinkedIn a cada etapa com um número que surpreendeu.

## Etapa 2: o que a primeira rodada mostrou

Split `dev`, 34 perguntas com artigo esperado. A busca densa reproduz exatamente os números do baseline, o que confirma que o executor de experimentos mede igual ao `evaluate.py`.

| Busca | Recall@5 | MRR | Recall@5 em termo exato | Recall@5 em leiga |
| --- | --- | --- | --- | --- |
| Densa (baseline) | 0,85 | 0,76 | 0,60 | 0,80 |
| BM25 | 0,50 | 0,35 | 0,60 | 0,00 |
| Híbrida (RRF, pesos iguais) | 0,56 | 0,45 | 0,40 | 0,20 |

A hipótese do roadmap ("a híbrida ganha nas perguntas de termo exato sem perder nas leigas") foi contrariada: a híbrida perdeu nas duas. Os motivos, olhando as perguntas uma a uma:

- **O nome da lei não está no texto do artigo.** O chunk guarda só o texto, então "Lei 14.133" na pergunta não ajuda o BM25 a separar o art. 75 da Lei 14.133 do art. 75 do CDC.
- **O número do artigo não basta para o BM25.** "Art. 75" aparece em outros 4 artigos que o citam, e o próprio art. 75 é longo; o BM25 penaliza texto longo e o deixou em 130º lugar.
- **O RRF premia consenso.** Na q057 a densa pôs o art. 75 em 1º, mas ele não estava entre os 50 do BM25; artigos medianos nas duas listas passaram à frente dele.
- **Pergunta leiga não tem palavras da lei.** O BM25 zera nas leigas, e com peso igual na fusão puxa a híbrida para baixo.

Hipóteses para a etapa 4, cada uma um experimento separado:

1. **Busca por referência.** Quando a pergunta cita "art. N" e uma lei, buscar o artigo direto pelo id e completar com a densa. Hipótese: termo exato sobe para perto de 1,00 sem mexer nas outras.
2. **Híbrida com peso.** Dar à densa peso maior na fusão. Hipótese: recupera a densa nas leigas e ganha alguns termos exatos.
3. **Cabeçalho no chunk.** Prefixar lei e número do artigo no texto indexado. Muda o chunking, então entra como experimento à parte.
4. **Reranker** (`bge-reranker-v2-m3`) sobre os 10 ou 20 primeiros da densa. Hipótese: melhora o MRR mais que o recall.

Com 5 perguntas de termo exato no `dev`, só uma diferença grande conta como sinal.

## Etapa 4: resultado

Mesmo split `dev`, mesmas 34 perguntas. Comando: `python -m rag_leis.experimento experiments/*.json`.

| Busca | Recall@5 | IC 95% | MRR | Termo exato (R@5 / MRR) | Leiga (R@5 / MRR) |
| --- | --- | --- | --- | --- | --- |
| Densa (baseline) | 0,85 | 0,73 a 0,96 | 0,76 | 0,60 / 0,45 | 0,80 / 0,53 |
| Híbrida, pesos 1 / 0,25 | 0,63 | 0,47 a 0,79 | 0,54 | 0,40 / 0,25 | 0,40 / 0,22 |
| Densa + artigo citado primeiro | 0,88 | 0,77 a 0,97 | 0,81 | 0,80 / 0,80 | 0,80 / 0,53 |
| Densa + reranker nos 20 primeiros | 0,90 | 0,79 a 0,97 | 0,80 | 0,60 / 0,40 | 0,90 / 0,73 |
| Densa + reranker + artigo citado | 0,93 | 0,84 a 1,00 | 0,86 | 0,80 / 0,80 | 0,90 / 0,73 |
| Densa com cabeçalho da lei | 0,90 | 0,79 a 0,98 | 0,79 | 0,80 / 0,50 | 0,80 / 0,60 |
| Cabeçalho + reranker + artigo citado | **0,94** | 0,85 a 1,00 | **0,89** | 0,80 / 0,80 | 0,90 / 0,78 |

O que cada hipótese deu:

1. **Busca por referência: confirmada.** No termo exato, o MRR foi de 0,45 para 0,80. Sobra a q063 ("inversão do ônus da prova"), que não cita número de artigo.
2. **Híbrida com peso: contrariada.** Mesmo com o BM25 valendo um quarto, ela fica abaixo da densa. Com c = 60 no RRF, a diferença entre o 1º e o 10º lugar da densa é pequena, e o BM25 basta para reordenar.
3. **Cabeçalho no chunk: confirmada.** Prefixar "Lei 8.078/1990 (Código de Defesa do Consumidor, CDC), art. 49 · capítulo" levou a densa de 0,85 para 0,90 no recall@5, sem custo na hora da pergunta. O BM25 com cabeçalho subiu pouco (0,50 para 0,53).
4. **Reranker: confirmada em parte.** Ele melhorou mais as leigas (MRR de 0,53 para 0,73) do que o termo exato, onde piorou um pouco. A q040 ("nome negativado") saiu de fora do top 5 para o 1º lugar; em troca, a q028 saiu do 1º lugar para fora do top 5.

As três peças se completam: o reranker ajuda nas leigas, a referência no termo exato e o cabeçalho em todos os tipos. Juntas dão a melhor linha, que é a busca "Completa" do app. Duas ressalvas:

- **Custo.** Com o reranker, cada pergunta leva cerca de 30 segundos a mais em CPU (39 perguntas em 19 minutos). Num atendimento real, isso pede GPU ou um reranker menor.
- **Escolha feita no dev.** A melhor configuração foi escolhida olhando o `dev`, então seu número é otimista. O valor para reportar sai do `test`, rodado uma única vez, junto com o baseline, no fim do projeto.

A busca está fechada por ora. O próximo passo é a geração (etapa 5), que depende do juiz validado.

## Como contar em entrevista

1. Montei um RAG sobre três leis brasileiras, com 406 artigos e um gabarito de 75 perguntas escrito antes de existir qualquer busca, dividido em dev e test.
2. A busca densa tem recall@5 de 0,85, mas cai para 0,60 nas perguntas de termo exato. Testei busca híbrida esperando ganhar nesse tipo, e ela piorou. O que funcionou foi combinar um reranker, que ajudou nas perguntas leigas, com uma regra que traz primeiro o artigo citado pelo número: somando o nome da lei no texto indexado, recall@5 de 0,94 no dev, ao custo de 30 segundos a mais por pergunta em CPU.
3. Descartei meu primeiro juiz LLM porque, numa sonda com respostas falsas de propósito, ele aprovou duas de três.
4. Em 8 de 34 perguntas o sistema disse que não sabia, embora o artigo certo estivesse nos trechos. Medir busca e geração separadamente mostrou que o problema estava na geração, e não na busca.
