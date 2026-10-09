# Validação do conjunto ouro

As 75 perguntas de `data/gold/gold.jsonl` foram redigidas por um LLM (Claude) a partir do texto do corpus. Pela regra 3 do roadmap, cada uma precisa ser lida e validada por você antes de valer como gabarito.

Para cada pergunta: abra o artigo indicado no `corpus.jsonl`, confira se a resposta esperada está apoiada no texto e se o artigo é mesmo o melhor para respondê-la. Marque a caixa, ou corrija a linha no `gold.jsonl`.

## Revisão por LLM (9 de outubro de 2026)

Segunda leitura feita pelo mesmo modelo que redigiu as perguntas (Claude). Não conta como validação humana e por isso as caixas abaixo continuam desmarcadas.

O que foi conferido:

- As 66 respostas com artigo esperado foram relidas contra o texto do artigo no corpus. Nenhum erro de fato encontrado.
- Prazos, percentuais e valores de cada resposta foram procurados no texto do artigo esperado. Todos aparecem (no CDC, por extenso: "trinta dias", "noventa dias", "cinco anos").
- Os temas das 9 perguntas fora do escopo foram procurados no corpus. Nenhum tem resposta lá.

Pontos para você decidir:

- **q031** (revogar consentimento): o artigo esperado é o `lgpd-art-8`, que traz a regra. Os arts. 15 e 18 da LGPD também citam a revogação, remetendo ao art. 8º. Se a busca trouxer só o 18, a métrica conta erro.
- **q045** (empresa punida): o esperado é o `licitacoes-art-14`. O `licitacoes-art-156` descreve a sanção de impedimento e também ajudaria a responder.
- **q063** (inversão do ônus da prova): o esperado é o `cdc-art-6`. O termo aparece também no `cdc-art-51`, como cláusula proibida.
- **q034** (com quem falar na empresa): o esperado é o `lgpd-art-41`. O `lgpd-art-5` traz a definição de encarregado.
- **q075** (Marco Civil): o `lgpd-art-60` cita o Marco Civil da Internet, mas não diz por quanto tempo os provedores guardam registros. Continua fora do escopo e é a mais difícil das nove, porque a busca vai trazer esse artigo.
- **q043 e q057** (dispensa por valor): as respostas usam R$ 50.000,00 e R$ 100.000,00, que são os valores do texto da lei. A atualização desses valores por decreto não está no corpus.

## Direta

- [ ] **q001** (dev) Qual é o objetivo da Lei Geral de Proteção de Dados Pessoais?
  - Artigos: `lgpd-art-1`
  - Resposta esperada: Proteger os direitos fundamentais de liberdade e de privacidade e o livre desenvolvimento da personalidade da pessoa natural, disciplinando o tratamento de dados pessoais, inclusive nos meios digitais.
- [ ] **q002** (test) A quais operações de tratamento de dados a LGPD se aplica?
  - Artigos: `lgpd-art-3`
  - Resposta esperada: A qualquer operação de tratamento, independentemente do meio, do país da sede ou de onde estejam os dados, desde que a operação seja realizada no território nacional, tenha por objetivo ofertar bens ou serviços ou tratar dados de indivíduos localizados no território nacional, ou os dados tenham sido coletados no território nacional.
- [ ] **q003** (dev) Quais princípios as atividades de tratamento de dados pessoais devem observar?
  - Artigos: `lgpd-art-6`
  - Resposta esperada: A boa-fé e os princípios da finalidade, adequação, necessidade, livre acesso, qualidade dos dados, transparência, segurança, prevenção, não discriminação e responsabilização e prestação de contas.
- [ ] **q004** (test) Em que hipóteses o tratamento de dados pessoais pode ser realizado?
  - Artigos: `lgpd-art-7`
  - Resposta esperada: Com consentimento do titular; para cumprimento de obrigação legal ou regulatória; pela administração pública para políticas públicas; para estudos por órgão de pesquisa; para execução de contrato; para exercício regular de direitos em processo; para proteção da vida ou da incolumidade física; para tutela da saúde; para atender a interesses legítimos do controlador ou de terceiro; e para proteção do crédito.
- [ ] **q005** (dev) Como o consentimento do titular deve ser fornecido?
  - Artigos: `lgpd-art-8`
  - Resposta esperada: Por escrito ou por outro meio que demonstre a manifestação de vontade do titular. Se for por escrito, deve constar de cláusula destacada das demais, e cabe ao controlador provar que o consentimento foi obtido conforme a lei.
- [ ] **q006** (test) Quais direitos o titular dos dados pode obter do controlador mediante requisição?
  - Artigos: `lgpd-art-18`
  - Resposta esperada: Confirmação da existência de tratamento; acesso aos dados; correção de dados incompletos, inexatos ou desatualizados; anonimização, bloqueio ou eliminação de dados desnecessários ou excessivos; portabilidade; eliminação dos dados tratados com consentimento; informação sobre com quem os dados foram compartilhados; informação sobre a possibilidade de não consentir; e revogação do consentimento.
- [ ] **q007** (dev) Quem responde pelos danos causados pelo tratamento de dados pessoais em violação à lei?
  - Artigos: `lgpd-art-42`
  - Resposta esperada: O controlador ou o operador que causar dano patrimonial, moral, individual ou coletivo é obrigado a repará-lo. O operador responde solidariamente quando descumpre a legislação ou não segue as instruções lícitas do controlador, e os controladores diretamente envolvidos respondem solidariamente.
- [ ] **q008** (test) Em que casos a transferência internacional de dados pessoais é permitida?
  - Artigos: `lgpd-art-33`
  - Resposta esperada: Entre outros casos, para países ou organismos internacionais com grau de proteção adequado; quando o controlador comprovar garantias como cláusulas contratuais específicas, cláusulas-padrão contratuais, normas corporativas globais ou selos e certificados; e quando necessária para cooperação jurídica internacional.
- [ ] **q009** (dev) Quais sanções administrativas podem ser aplicadas a quem descumpre a LGPD?
  - Artigos: `lgpd-art-52`
  - Resposta esperada: Advertência; multa simples de até 2% do faturamento, limitada a R$ 50 milhões por infração; multa diária; publicização da infração; bloqueio e eliminação dos dados; suspensão parcial do banco de dados ou da atividade de tratamento por até 6 meses, prorrogável; e proibição parcial ou total das atividades de tratamento.
- [ ] **q010** (test) Quem a lei considera consumidor?
  - Artigos: `cdc-art-2`
  - Resposta esperada: Toda pessoa física ou jurídica que adquire ou utiliza produto ou serviço como destinatário final. Equipara-se a consumidor a coletividade de pessoas, ainda que indetermináveis, que haja intervindo nas relações de consumo.
- [ ] **q011** (dev) Quem a lei considera fornecedor?
  - Artigos: `cdc-art-3`
  - Resposta esperada: Toda pessoa física ou jurídica, pública ou privada, nacional ou estrangeira, e os entes despersonalizados, que desenvolvem atividade de produção, montagem, criação, construção, transformação, importação, exportação, distribuição ou comercialização de produtos ou prestação de serviços.
- [ ] **q012** (test) Em quanto tempo caduca o direito de reclamar de vícios aparentes de produtos e serviços?
  - Artigos: `cdc-art-26`
  - Resposta esperada: Em 30 dias para serviços e produtos não duráveis e em 90 dias para serviços e produtos duráveis, contados da entrega efetiva do produto ou do término da execução do serviço. No vício oculto, o prazo começa quando o defeito fica evidenciado.
- [ ] **q013** (dev) Qual é o prazo de prescrição para pedir reparação por danos causados por fato do produto ou do serviço?
  - Artigos: `cdc-art-27`
  - Resposta esperada: Cinco anos, contados do conhecimento do dano e de sua autoria.
- [ ] **q014** (test) Por quanto tempo fabricantes e importadores devem oferecer peças de reposição?
  - Artigos: `cdc-art-32`
  - Resposta esperada: Enquanto não cessar a fabricação ou a importação do produto. Depois disso, a oferta deve ser mantida por período razoável de tempo, na forma da lei.
- [ ] **q015** (dev) O que é publicidade enganosa?
  - Artigos: `cdc-art-37`
  - Resposta esperada: Qualquer informação ou comunicação publicitária inteira ou parcialmente falsa, ou capaz, mesmo por omissão, de induzir o consumidor em erro sobre natureza, características, qualidade, quantidade, propriedades, origem, preço ou outros dados de produtos e serviços. Ela é proibida.
- [ ] **q016** (test) Como devem ser interpretadas as cláusulas dos contratos de consumo?
  - Artigos: `cdc-art-47`
  - Resposta esperada: De maneira mais favorável ao consumidor.
- [ ] **q017** (dev) Qual é o limite da multa de mora por atraso no pagamento de prestações em contratos de crédito ao consumidor?
  - Artigos: `cdc-art-52`
  - Resposta esperada: Dois por cento do valor da prestação.
- [ ] **q018** (test) O que a lei entende por superendividamento?
  - Artigos: `cdc-art-54-A`
  - Resposta esperada: A impossibilidade manifesta de o consumidor pessoa natural, de boa-fé, pagar a totalidade de suas dívidas de consumo, exigíveis e vincendas, sem comprometer seu mínimo existencial.
- [ ] **q019** (dev) Quais são as fases do processo de licitação?
  - Artigos: `licitacoes-art-17`
  - Resposta esperada: Em sequência: preparatória; divulgação do edital; apresentação de propostas e lances, quando for o caso; julgamento; habilitação; recursal; e homologação.
- [ ] **q020** (test) Quais são as modalidades de licitação?
  - Artigos: `licitacoes-art-28`
  - Resposta esperada: Pregão, concorrência, concurso, leilão e diálogo competitivo. É vedado criar outras modalidades ou combinar essas.
- [ ] **q021** (dev) Quais são os critérios de julgamento das propostas em uma licitação?
  - Artigos: `licitacoes-art-33`
  - Resposta esperada: Menor preço; maior desconto; melhor técnica ou conteúdo artístico; técnica e preço; maior lance, no caso de leilão; e maior retorno econômico.
- [ ] **q022** (test) Em que prazo o contrato administrativo deve ser divulgado no Portal Nacional de Contratações Públicas?
  - Artigos: `licitacoes-art-94`
  - Resposta esperada: Em 20 dias úteis no caso de licitação e em 10 dias úteis no caso de contratação direta, contados da assinatura. A divulgação é condição indispensável para a eficácia do contrato.
- [ ] **q023** (dev) Qual pode ser o valor da garantia exigida nas contratações de obras, serviços e fornecimentos?
  - Artigos: `licitacoes-art-98`
  - Resposta esperada: Até 5% do valor inicial do contrato, podendo chegar a 10% se justificado pela complexidade técnica e pelos riscos envolvidos.
- [ ] **q024** (test) Até que limite o contratado é obrigado a aceitar acréscimos ou supressões determinados unilateralmente pela Administração?
  - Artigos: `licitacoes-art-125`
  - Resposta esperada: Até 25% do valor inicial atualizado do contrato. No caso de reforma de edifício ou de equipamento, o limite para acréscimos é de 50%.
- [ ] **q025** (dev) Quais sanções podem ser aplicadas ao responsável por infrações administrativas em licitações e contratos?
  - Artigos: `licitacoes-art-156`
  - Resposta esperada: Advertência, multa, impedimento de licitar e contratar e declaração de inidoneidade para licitar ou contratar.
- [ ] **q026** (test) Quais são os limites mínimo e máximo da multa aplicada por infração administrativa em licitações?
  - Artigos: `licitacoes-art-156`
  - Resposta esperada: A multa não pode ser inferior a 0,5% nem superior a 30% do valor do contrato licitado ou celebrado com contratação direta.
- [ ] **q027** (dev) Qual é o prazo para recorrer do julgamento das propostas em uma licitação?
  - Artigos: `licitacoes-art-165`
  - Resposta esperada: Três dias úteis, contados da data de intimação ou de lavratura da ata.

## Linguagem leiga

- [ ] **q028** (dev) Cancelei minha conta num aplicativo. A empresa pode continuar guardando meus dados?
  - Artigos: `lgpd-art-16`
  - Resposta esperada: Em regra não: os dados devem ser eliminados após o término do tratamento. A conservação só é autorizada para cumprir obrigação legal ou regulatória, para estudo por órgão de pesquisa, para transferência a terceiro dentro das regras da lei, ou para uso exclusivo do controlador com os dados anonimizados.
- [ ] **q029** (test) Um sistema automático recusou meu pedido de crédito. Posso pedir que essa decisão seja reavaliada?
  - Artigos: `lgpd-art-20`
  - Resposta esperada: Sim. O titular tem direito de solicitar a revisão de decisões tomadas unicamente com base em tratamento automatizado que afetem seus interesses, inclusive as de perfil de crédito, e de receber informações claras sobre os critérios usados.
- [ ] **q030** (dev) Um joguinho de celular pode coletar os dados do meu filho de 8 anos sem a minha autorização?
  - Artigos: `lgpd-art-14`
  - Resposta esperada: Não. O tratamento de dados de crianças exige consentimento específico e em destaque de pelo menos um dos pais ou do responsável legal. A exceção é a coleta para contatar os pais ou para proteção da criança, sem armazenamento. O jogo também não pode exigir mais dados do que o estritamente necessário.
- [ ] **q031** (test) Autorizei uma empresa a usar meus dados e me arrependi. Dá para voltar atrás?
  - Artigos: `lgpd-art-8`
  - Resposta esperada: Sim. O consentimento pode ser revogado a qualquer momento, por manifestação expressa do titular, em procedimento gratuito e facilitado.
- [ ] **q032** (dev) Houve um vazamento numa loja onde tenho cadastro. A loja é obrigada a me avisar?
  - Artigos: `lgpd-art-48`
  - Resposta esperada: Sim, quando o incidente puder acarretar risco ou dano relevante. O controlador deve comunicar à autoridade nacional e ao titular, em prazo razoável, informando os dados afetados, os riscos e as medidas adotadas.
- [ ] **q033** (test) Pedi para uma empresa me dizer quais dados meus ela tem. Em quanto tempo ela precisa responder?
  - Artigos: `lgpd-art-19`
  - Resposta esperada: Imediatamente, em formato simplificado, ou em até 15 dias, por meio de declaração clara e completa, contados da data do requerimento.
- [ ] **q034** (dev) Com quem eu falo dentro de uma empresa para reclamar de como ela usa os meus dados?
  - Artigos: `lgpd-art-41`
  - Resposta esperada: Com o encarregado pelo tratamento de dados pessoais, que o controlador deve indicar. A identidade e o contato do encarregado devem ser divulgados publicamente, de preferência no site, e cabe a ele receber reclamações dos titulares.
- [ ] **q035** (test) Comprei pela internet e me arrependi, posso devolver?
  - Artigos: `cdc-art-49`
  - Resposta esperada: Sim. O consumidor pode desistir em até 7 dias a contar da assinatura ou do recebimento do produto, quando a contratação ocorre fora do estabelecimento comercial, e os valores pagos são devolvidos de imediato, monetariamente atualizados.
- [ ] **q036** (dev) Chegou na minha casa um produto que eu nunca pedi. Sou obrigado a pagar?
  - Artigos: `cdc-art-39`
  - Resposta esperada: Não. Enviar produto sem solicitação prévia é prática abusiva, e o produto entregue nessa condição equipara-se a amostra grátis, sem obrigação de pagamento.
- [ ] **q037** (test) Paguei uma cobrança que veio errada na fatura. Tenho direito de receber o dinheiro de volta?
  - Artigos: `cdc-art-42`
  - Resposta esperada: Sim. O consumidor cobrado em quantia indevida tem direito à devolução em dobro do que pagou em excesso, com correção monetária e juros legais, salvo engano justificável.
- [ ] **q038** (dev) A loja anunciou um preço e na hora se recusou a vender por ele. O que eu posso fazer?
  - Artigos: `cdc-art-35`
  - Resposta esperada: O consumidor pode escolher entre exigir o cumprimento forçado da oferta, aceitar outro produto ou serviço equivalente, ou rescindir o contrato com restituição do que pagou, atualizado, e perdas e danos.
- [ ] **q039** (test) Meu celular novo deu defeito e a assistência não consertou em mais de um mês. Quais são as minhas opções?
  - Artigos: `cdc-art-18`
  - Resposta esperada: Se o vício não for sanado em 30 dias, o consumidor pode exigir, à sua escolha, a substituição do produto por outro da mesma espécie em perfeitas condições, a restituição imediata da quantia paga, atualizada, ou o abatimento proporcional do preço.
- [ ] **q040** (dev) Meu nome está negativado por uma dívida antiga. Por quanto tempo isso pode ficar registrado?
  - Artigos: `cdc-art-43`
  - Resposta esperada: Os cadastros de consumidores não podem conter informações negativas referentes a período superior a cinco anos.
- [ ] **q041** (test) A loja me deu um ano de garantia. Isso vale no lugar da garantia que a lei já dá?
  - Artigos: `cdc-art-50`
  - Resposta esperada: Não. A garantia contratual é complementar à legal e deve ser conferida mediante termo escrito.
- [ ] **q042** (dev) O banco fica me ligando e insistindo para eu pegar um empréstimo, e eu sou idoso. Isso é permitido?
  - Artigos: `cdc-art-54-C`
  - Resposta esperada: Não. Na oferta de crédito é vedado assediar ou pressionar o consumidor para contratar, principalmente se for idoso, analfabeto, doente ou estiver em estado de vulnerabilidade.
- [ ] **q043** (test) A prefeitura precisa fazer licitação para uma compra pequena, de uns 30 mil reais?
  - Artigos: `licitacoes-art-75`
  - Resposta esperada: Não necessariamente. A licitação é dispensável para compras e outros serviços de valor inferior a R$ 50.000,00, segundo o texto da lei.
- [ ] **q044** (dev) A cidade quer contratar um cantor famoso para a festa de aniversário. Precisa fazer licitação?
  - Artigos: `licitacoes-art-74`
  - Resposta esperada: Não. A licitação é inexigível para contratar profissional do setor artístico, diretamente ou por empresário exclusivo, desde que consagrado pela crítica especializada ou pela opinião pública.
- [ ] **q045** (test) Uma empresa que está cumprindo punição pode entrar em uma nova licitação?
  - Artigos: `licitacoes-art-14`
  - Resposta esperada: Não. Não pode disputar licitação quem, ao tempo da licitação, esteja impossibilitado de participar em decorrência de sanção que lhe foi imposta.
- [ ] **q046** (dev) Onde encontro os editais de licitação que o governo publica?
  - Artigos: `licitacoes-art-54`
  - Resposta esperada: No Portal Nacional de Contratações Públicas (PNCP), onde o inteiro teor do edital e de seus anexos deve ser divulgado e mantido. Também é obrigatória a publicação de extrato no Diário Oficial e em jornal diário de grande circulação.

## Vários artigos

- [ ] **q047** (dev) O tratamento de dados pessoais sensíveis sem consentimento é permitido nas mesmas hipóteses que o de dados pessoais comuns?
  - Artigos: `lgpd-art-7`, `lgpd-art-11`
  - Resposta esperada: Não. Para dados sensíveis, a dispensa de consentimento só vale quando indispensável para obrigação legal, políticas públicas, estudos por órgão de pesquisa, exercício regular de direitos, proteção da vida, tutela da saúde ou prevenção à fraude. Hipóteses admitidas para dados comuns, como interesse legítimo e proteção do crédito, não aparecem na lista dos dados sensíveis.
- [ ] **q048** (test) Quando o tratamento de dados pessoais termina e o que deve acontecer com os dados depois disso?
  - Artigos: `lgpd-art-15`, `lgpd-art-16`
  - Resposta esperada: O tratamento termina quando a finalidade é alcançada ou os dados deixam de ser necessários, ao fim do período de tratamento, por comunicação do titular ou por determinação da autoridade nacional. Depois disso os dados devem ser eliminados, salvo conservação para obrigação legal, pesquisa, transferência a terceiro ou uso exclusivo do controlador com dados anonimizados.
- [ ] **q049** (dev) Quem é o encarregado pelo tratamento de dados e quais são as suas atividades?
  - Artigos: `lgpd-art-5`, `lgpd-art-41`
  - Resposta esperada: É a pessoa indicada para atuar como canal de comunicação entre o controlador, os titulares e a autoridade nacional. Cabe a ele aceitar reclamações e comunicações dos titulares, receber comunicações da autoridade nacional e orientar funcionários e contratados sobre proteção de dados.
- [ ] **q050** (test) Quais são os prazos para o consumidor reclamar de um vício do produto e para pedir indenização por um acidente de consumo?
  - Artigos: `cdc-art-26`, `cdc-art-27`
  - Resposta esperada: Para vícios aparentes, 30 dias para produtos e serviços não duráveis e 90 dias para duráveis. Para reparação de danos por fato do produto ou do serviço, cinco anos a partir do conhecimento do dano e de sua autoria.
- [ ] **q051** (dev) O fornecedor é obrigado a cumprir o que anuncia? O que o consumidor pode fazer se ele não cumprir?
  - Artigos: `cdc-art-30`, `cdc-art-35`
  - Resposta esperada: Sim. Toda informação ou publicidade suficientemente precisa obriga o fornecedor e integra o contrato. Se ele recusar, o consumidor pode exigir o cumprimento forçado, aceitar produto ou serviço equivalente, ou rescindir o contrato com restituição e perdas e danos.
- [ ] **q052** (test) Quem responde pelos danos causados por defeito de um produto e por defeito de um serviço? É preciso provar culpa?
  - Artigos: `cdc-art-12`, `cdc-art-14`
  - Resposta esperada: Pelo produto respondem o fabricante, o produtor, o construtor e o importador; pelo serviço, o fornecedor de serviços. Em ambos os casos a responsabilidade independe da existência de culpa.
- [ ] **q053** (dev) Em que situações a Administração pode contratar sem fazer licitação?
  - Artigos: `licitacoes-art-74`, `licitacoes-art-75`
  - Resposta esperada: Quando a licitação é inexigível, por ser inviável a competição, como no fornecedor exclusivo, no artista consagrado e nos serviços técnicos de notória especialização; e quando é dispensável, como nas contratações de pequeno valor e nas demais hipóteses listadas na lei.
- [ ] **q054** (test) A Administração pode alterar o contrato sozinha? Até que ponto a empresa contratada é obrigada a aceitar?
  - Artigos: `licitacoes-art-124`, `licitacoes-art-125`
  - Resposta esperada: Sim. A Administração pode alterar unilateralmente o contrato quando houver modificação do projeto ou das especificações ou quando for necessário acrescer ou diminuir quantidades. O contratado é obrigado a aceitar acréscimos ou supressões de até 25% do valor inicial atualizado, ou acréscimos de até 50% em reforma de edifício ou de equipamento.
- [ ] **q055** (dev) Por quanto tempo pode durar um contrato de serviço contínuo, como o de limpeza, e ele pode ser renovado?
  - Artigos: `licitacoes-art-106`, `licitacoes-art-107`
  - Resposta esperada: O contrato de serviços e fornecimentos contínuos pode ser celebrado por até 5 anos e prorrogado sucessivamente, respeitada a vigência máxima de dez anos, desde que haja previsão em edital e as condições e os preços permaneçam vantajosos.
- [ ] **q056** (test) Que condutas de um licitante são infrações administrativas e quais punições ele pode receber?
  - Artigos: `licitacoes-art-155`, `licitacoes-art-156`
  - Resposta esperada: São infrações, entre outras, dar causa à inexecução parcial ou total do contrato, deixar de entregar a documentação exigida, não manter a proposta, não celebrar o contrato e apresentar declaração ou documentação falsa. As sanções são advertência, multa, impedimento de licitar e contratar e declaração de inidoneidade.

## Termo exato

- [ ] **q057** (dev) O que diz o art. 75 da Lei 14.133?
  - Artigos: `licitacoes-art-75`
  - Resposta esperada: Lista as hipóteses em que a licitação é dispensável, entre elas contratações inferiores a R$ 100.000,00 para obras e serviços de engenharia ou manutenção de veículos e inferiores a R$ 50.000,00 para outros serviços e compras.
- [ ] **q058** (test) O que diz o art. 5º da Lei 14.133/2021?
  - Artigos: `licitacoes-art-5`
  - Resposta esperada: Enumera os princípios a observar na aplicação da lei, como legalidade, impessoalidade, moralidade, publicidade, eficiência, interesse público, planejamento, transparência, segregação de funções, vinculação ao edital, julgamento objetivo e competitividade.
- [ ] **q059** (dev) O que dispõe o art. 193 da Lei 14.133?
  - Artigos: `licitacoes-art-193`
  - Resposta esperada: Revoga os arts. 89 a 108 da Lei 8.666/1993 na data de publicação e, em 30 de dezembro de 2023, a Lei 8.666/1993, a Lei 10.520/2002 e os arts. 1º a 47-A da Lei 12.462/2011.
- [ ] **q060** (test) Como a Lei 14.133 define sistema de registro de preços?
  - Artigos: `licitacoes-art-6`
  - Resposta esperada: Conjunto de procedimentos para realização, mediante contratação direta ou licitação nas modalidades pregão ou concorrência, de registro formal de preços relativos a prestação de serviços, a obras e a aquisição e locação de bens para contratações futuras.
- [ ] **q061** (dev) O que dispõe o art. 51 do Código de Defesa do Consumidor?
  - Artigos: `cdc-art-51`
  - Resposta esperada: Declara nulas de pleno direito cláusulas contratuais abusivas, como as que exonerem ou atenuem a responsabilidade do fornecedor, subtraiam a opção de reembolso, transfiram responsabilidades a terceiros ou coloquem o consumidor em desvantagem exagerada.
- [ ] **q062** (test) O que estabelece o art. 42-A da Lei 8.078/1990?
  - Artigos: `cdc-art-42-A`
  - Resposta esperada: Que todos os documentos de cobrança de débitos apresentados ao consumidor devem trazer o nome, o endereço e o CPF ou CNPJ do fornecedor do produto ou serviço.
- [ ] **q063** (dev) O que o Código de Defesa do Consumidor diz sobre a inversão do ônus da prova?
  - Artigos: `cdc-art-6`
  - Resposta esperada: É direito básico do consumidor a facilitação da defesa de seus direitos, inclusive com a inversão do ônus da prova a seu favor no processo civil, quando, a critério do juiz, for verossímil a alegação ou quando ele for hipossuficiente.
- [ ] **q064** (test) O que diz o art. 46 da LGPD?
  - Artigos: `lgpd-art-46`
  - Resposta esperada: Que os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas, aptas a proteger os dados pessoais de acessos não autorizados e de situações acidentais ou ilícitas de destruição, perda, alteração, comunicação ou tratamento inadequado.
- [ ] **q065** (dev) Qual é o conteúdo do art. 37 da Lei 13.709/2018?
  - Artigos: `lgpd-art-37`
  - Resposta esperada: O controlador e o operador devem manter registro das operações de tratamento de dados pessoais que realizarem, especialmente quando baseado no legítimo interesse.
- [ ] **q066** (test) Como a LGPD define dado pessoal sensível?
  - Artigos: `lgpd-art-5`
  - Resposta esperada: Dado pessoal sobre origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou a organização de caráter religioso, filosófico ou político, dado referente à saúde ou à vida sexual, dado genético ou biométrico, quando vinculado a uma pessoa natural.

## Fora do escopo

- [ ] **q067** (dev) Qual o prazo para entrar com ação trabalhista?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
- [ ] **q068** (test) Quais são os requisitos para pedir aposentadoria por idade?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
- [ ] **q069** (dev) Qual é a pena prevista para o crime de furto?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
- [ ] **q070** (test) Como funciona a partilha de bens no divórcio?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
- [ ] **q071** (dev) Em quanto tempo o inquilino precisa desocupar o imóvel depois de uma ordem de despejo?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
- [ ] **q072** (test) Quais são as alíquotas do imposto de renda da pessoa física?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
- [ ] **q073** (dev) Quantos dias de licença-maternidade a lei garante?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
- [ ] **q074** (test) Qual é o limite de velocidade nas rodovias?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
- [ ] **q075** (dev) Por quanto tempo o Marco Civil da Internet obriga os provedores a guardar registros de conexão?
  - Artigos: nenhum
  - Resposta esperada: Não encontrei na base.
