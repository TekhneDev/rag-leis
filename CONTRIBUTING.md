# Como contribuir

Obrigada pelo interesse no rag-leis. Este é um projeto de estudo e portfólio, com **todos os direitos reservados** (veja [`LICENSE`](LICENSE)). Por isso, a forma mais útil de contribuir é **apontar problemas**; mudanças de código são aceitas só depois de combinadas numa issue.

Ao participar, você concorda em seguir o [código de conduta](CODE_OF_CONDUCT.md).

## O que é mais útil

| Contribuição | Como fazer |
| --- | --- |
| Erro no conjunto ouro (resposta esperada errada, artigo errado, pergunta ambígua) | Issue com o modelo **Erro no gabarito** |
| Resposta do sistema que contradiz a lei | Issue com o modelo **Resposta errada** |
| Bug no código, no app ou nos comandos do README | Issue com o modelo **Bug** |
| Ideia de experimento | Issue com o modelo **Ideia de experimento**, com a hipótese e a métrica que mudaria |
| Falha de segurança | **Não abra issue.** Siga a [política de segurança](SECURITY.md) |

Dúvidas sobre o seu caso jurídico pessoal estão fora do escopo: o sistema é um estudo e não substitui orientação jurídica.

## Antes de propor uma mudança de código

1. Abra uma issue descrevendo o problema e a mudança. Espere a resposta da mantenedora antes de escrever código.
2. Se a mudança for aceita, faça um fork, crie um branch a partir de `main` e abra um pull request referenciando a issue.

Pull requests sem issue combinada podem ser fechados sem revisão.

## Termos das contribuições

Ao enviar um pull request, um comentário com código ou uma correção do gabarito, você declara que o conteúdo é de sua autoria e autoriza a autora do projeto a usá-lo, modificá-lo e distribuí-lo como parte do rag-leis, sob os termos que ela escolher, sem compensação. Você mantém o direito de usar a sua própria contribuição em outros lugares. Contribuir não dá direito de uso sobre o restante do projeto.

## Ambiente de desenvolvimento

O passo a passo completo está em [Como rodar](README.md#como-rodar). Resumo:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev,app]"
python -m rag_leis.index --cabecalho
```

Antes de abrir o pull request, os três comandos abaixo precisam passar. O CI roda os mesmos a cada push:

```bash
ruff check .
black --check .
pytest
```

## Regras do projeto

Estas regras protegem a validade dos resultados. Uma mudança que quebre alguma delas não será aceita, mesmo que melhore um número.

1. **O split `test` não é olhado.** Ajustes são feitos só com o `dev`. O `test` será rodado uma única vez, no fim do projeto. Não abra, não rode e não cite resultados do `test`.
2. **Uma peça por experimento.** Cada experimento muda uma coisa em relação a uma configuração existente e vira um arquivo em `experiments/`. Combinações entram como experimentos próprios.
3. **Todo número sai de um comando.** Resultados novos vêm de `python -m rag_leis.experimento` ou de `python -m rag_leis.evaluate`, gravados em `results/`. Não edite `results/experimentos/tabela.md` à mão.
4. **O gabarito muda só com justificativa.** Correções no `data/gold/gold.jsonl` citam o artigo e o trecho do texto que as apoia, e são registradas em `results/validacao_gold.md`.
5. **LLM com temperatura zero e saídas salvas.** Nenhuma métrica depende de uma chamada que não ficou gravada em disco.
6. **Sem chaves no repositório.** Chaves de API, se um dia existirem, ficam num `.env`, que está no `.gitignore`.

## Estilo

- **Código:** Python 3.10 ou mais recente, formatado com `black` e conferido com `ruff`. Nomes de funções, variáveis e mensagens em português, como no resto do código. Docstrings curtas que dizem o que a função devolve.
- **Testes:** toda função nova de lógica pura ganha um teste em `tests/`. Testes não podem depender do Ollama, de download de modelo ou do índice.
- **Commits:** em português, no imperativo da terceira pessoa e começando com verbo, como no histórico (`Adiciona reranker...`, `Corrige ids...`). Assunto curto; o corpo explica o porquê quando não for óbvio.
- **Documentos:** frases diretas, números com vírgula decimal e o split sempre indicado (`dev`).

## Revisão

A mantenedora revisa quando puder, sem prazo garantido. Uma contribuição pode ser recusada mesmo correta, se não couber no escopo do projeto.
