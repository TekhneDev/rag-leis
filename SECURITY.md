# Política de segurança

## Versões cobertas

O projeto não tem releases. Só a versão atual do branch `main` recebe correções de segurança.

## Como relatar uma vulnerabilidade

**Não abra uma issue pública.** Use o relato privado do GitHub:

1. Abra https://github.com/TekhneDev/rag-leis/security/advisories/new, ou vá em **Security → Report a vulnerability** no repositório.
2. Descreva o problema, como reproduzir, o impacto e, se tiver, uma sugestão de correção.

O relato fica visível só para você e para a mantenedora.

## O que esperar

- Confirmação de recebimento em até 7 dias.
- Uma avaliação inicial, dizendo se o problema foi aceito e qual a gravidade, em até 14 dias.
- Se aceito, a correção é feita no `main` e o relato é publicado como advisory, com crédito a quem relatou, se a pessoa quiser.

Como é um projeto pessoal de estudo, esses prazos são o objetivo, não uma garantia.

## Escopo

Entram no escopo, por exemplo:

- Execução de código ou leitura de arquivos da máquina por meio do app ou dos comandos do projeto.
- Dependências com vulnerabilidade conhecida que afete o uso do projeto.
- Chaves, tokens ou dados pessoais publicados no repositório por engano.
- Falhas no CI que permitam alterar o código publicado.

Ficam fora do escopo:

- Respostas jurídicas erradas ou inventadas pelo modelo. São limitações conhecidas de um estudo; relate como issue de **Resposta errada**.
- Vulnerabilidades do Ollama, do Streamlit, dos modelos ou de outras bibliotecas sem impacto específico neste projeto. Relate ao projeto de origem.
- Ataques que exigem acesso prévio à máquina de quem roda o sistema.

## Recomendações para quem roda o projeto

- **O app foi feito para uso local.** Por padrão, o Streamlit aceita conexões de outras máquinas da rede. Para limitar ao próprio computador, rode:

  ```bash
  streamlit run app.py --server.address localhost
  ```

  Não exponha o app ou o Ollama na internet sem autenticação.
- **Os modelos vêm do Hugging Face e do Ollama.** Use só os nomes indicados no README e confira a origem antes de trocar por outro modelo.
- **Chaves de API** ficam num arquivo `.env`, que está no `.gitignore`. Nunca as coloque no código ou nas configurações de `experiments/`.
- **Não digite dados pessoais reais** nas perguntas. Tudo roda localmente, mas as perguntas podem ficar em logs do terminal e do Ollama.
