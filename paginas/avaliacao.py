"""Página de avaliação do app: métricas, evolução e erros, só do split dev."""

import textwrap

import altair as alt
import pandas as pd
import streamlit as st

from paginas.estilo import cabeca
from rag_leis.painel import (
    EVOLUCAO,
    NOMES_DAS_METRICAS,
    NOMES_DOS_TIPOS,
    RODADAS,
    estado_do_juiz,
    evolucao_da_busca,
    experimentos,
    linhas_de_metrica,
    metricas_da_rodada,
    mudancas,
    numero,
    por_pergunta,
)

# Grafite para a busca atual do app, cinza para o ponto de partida.
CORES = {"Completa (app)": "#1C1F26", "Baseline (densa)": "#A3A7AE"}
CORES_DA_EVOLUCAO = ["#1C1F26", "#8A2432", "#24507A"]
METRICAS_DA_RESPOSTA = [
    "abstencao_indevida",
    "correta",
    "fiel",
    "cita_artigo",
    "citacoes_nos_trechos",
    "abstencao_correta",
]
ESCALA = alt.Scale(domain=[0, 1])
# Rótulos de eixo com "|" viram várias linhas, para caber no celular sem cortar.
EM_LINHAS = "split(datum.label, '|')"
PAPEIS = {
    "busca_densa": "Baseline",
    "busca_densa_cabecalho_referencia": "App: Rápida",
    "busca_densa_cabecalho_reranker_referencia": "App: Completa",
}


@st.cache_data
def carregar():
    rodadas = {rodada: metricas_da_rodada(rodada) for rodada in RODADAS}
    return rodadas, experimentos(), por_pergunta(), estado_do_juiz()


def valor(metricas: dict, metrica: str, tipo: str = "geral") -> dict:
    return metricas[tipo][metrica]


def fracao(metricas: dict, metrica: str, tipo: str = "geral") -> str:
    """ "8 de 34", contando pela média e pelo número de perguntas."""
    item = valor(metricas, metrica, tipo)
    return f"{round(item['media'] * item['n'])} de {item['n']}"


def quebrar(texto: str, largura: int = 18) -> str:
    """Quebra um rótulo em linhas de até `largura` caracteres, separadas por "|"."""
    return "|".join(textwrap.wrap(texto, largura))


def comparacao(rodadas: dict, metricas: list[str], tipo: str = "geral") -> pd.DataFrame:
    linhas = []
    for rodada, nome in RODADAS.items():
        for metrica in metricas:
            item = rodadas[rodada].get(tipo, {}).get(metrica)
            if item:
                linhas.append(
                    {
                        "rodada": nome,
                        "metrica": NOMES_DAS_METRICAS[metrica],
                        "media": item["media"],
                        "baixo": item["ic95"][0],
                        "alto": item["ic95"][1],
                        "n": item["n"],
                    }
                )
    return pd.DataFrame(linhas)


def barras_com_intervalo(dados: pd.DataFrame, categoria: str, titulo: str):
    """Barras horizontais lado a lado por rodada, com o intervalo de 95%."""
    dados = dados.assign(rotulo=dados[categoria].map(quebrar))
    base = alt.Chart(dados).encode(
        y=alt.Y("rotulo:N", title=None, sort=None, axis=alt.Axis(labelExpr=EM_LINHAS)),
        yOffset=alt.YOffset("rodada:N", sort=list(CORES)),
        tooltip=[
            alt.Tooltip(f"{categoria}:N", title=titulo),
            alt.Tooltip("rodada:N", title="Rodada"),
            alt.Tooltip("media:Q", title="Média", format=".2f"),
            alt.Tooltip("baixo:Q", title="IC 95% de", format=".2f"),
            alt.Tooltip("alto:Q", title="até", format=".2f"),
            alt.Tooltip("n:Q", title="Perguntas"),
        ],
    )
    barras = base.mark_bar(cornerRadiusEnd=4, height={"band": 0.9}).encode(
        x=alt.X("media:Q", title="Média", scale=ESCALA),
        color=alt.Color(
            "rodada:N",
            title=None,
            scale=alt.Scale(domain=list(CORES), range=list(CORES.values())),
            legend=alt.Legend(orient="top"),
        ),
    )
    intervalos = base.mark_rule(strokeWidth=1.5, opacity=0.6).encode(
        x="baixo:Q", x2="alto:Q"
    )
    return (barras + intervalos).properties(height=alt.Step(20))


def posicao(pergunta: dict, rodada: str) -> str:
    """Posição do artigo esperado, "fora" se não veio entre os 5, vazio fora do escopo."""
    if pergunta["tipo"] == "fora_do_escopo":
        return ""
    return str(pergunta[f"{rodada}_posicao"] or "fora")


rodadas, registros, perguntas, juiz = carregar()
baseline, completa = rodadas["baseline"], rodadas["completa"]
trocas = mudancas(perguntas)

cabeca(
    "Qualidade medida",
    "Como o sistema se sai em perguntas com resposta conhecida, escritas antes de ele "
    "existir, e como chegou até aqui. Tudo é do split dev: 39 perguntas, 34 com artigo "
    "esperado e 5 fora do escopo. O split test fica fechado até a medição final.",
)

# Resumo: a busca do app contra o baseline.
st.subheader("Resumo: busca completa contra o baseline")
colunas = st.columns(4)
for coluna, metrica, menor_e_melhor, ajuda in [
    (
        colunas[0],
        "recall@5",
        False,
        "Fração dos artigos esperados entre os 5 trazidos.",
    ),
    (
        colunas[1],
        "abstencao_indevida",
        True,
        'Perguntas com resposta no corpus em que o sistema disse "Não encontrei".',
    ),
    (colunas[2], "correta", False, "Resposta bate com a esperada, segundo o juiz LLM."),
    (
        colunas[3],
        "citacoes_nos_trechos",
        False,
        "Respostas que citam só artigos que o modelo recebeu.",
    ),
]:
    antes, depois = valor(baseline, metrica)["media"], valor(completa, metrica)["media"]
    coluna.metric(
        NOMES_DAS_METRICAS[metrica],
        numero(depois),
        # O Streamlit escolhe a seta e a cor pelo "-" (hífen comum) no começo do texto.
        delta=f"{'+' if depois >= antes else '-'}{numero(abs(depois - antes))}",
        delta_color="inverse" if menor_e_melhor else "normal",
        help=f"{ajuda} Baseline: {numero(antes)}.",
        border=True,
    )

melhor = max(registros, key=lambda r: r["metricas"]["geral"]["mrr"]["media"])
st.markdown(f"""
**O que os números dizem**

- **A busca melhorou e o ganho chegou à resposta.** O recall@5 foi de
  {numero(valor(baseline, "recall@5")["media"])} para
  {numero(valor(completa, "recall@5")["media"])}, e a abstenção indevida caiu de
  {fracao(baseline, "abstencao_indevida")} para
  {fracao(completa, "abstencao_indevida")} perguntas. Nas perguntas em linguagem
  leiga, de {fracao(baseline, "abstencao_indevida", "leiga")} para
  {fracao(completa, "abstencao_indevida", "leiga")}.
- **A correção subiu menos do que a busca.** {len(trocas["passou_a_correta"])}
  perguntas passaram a ser respondidas certo e
  {len(trocas["deixou_de_ser_correta"])} passaram a errado. Com 34 perguntas, os
  intervalos ainda se sobrepõem.
- **O custo apareceu nas citações.** {len(trocas["cita_fora_dos_trechos"])}
  resposta(s) da busca completa citam artigo que o modelo não recebeu
  ({", ".join(trocas["cita_fora_dos_trechos"]) or "nenhuma"}). O próximo passo é o
  prompt, não a busca.
- **O sistema não inventa fora do escopo.** Nas 5 perguntas sobre outras leis, as
  duas rodadas disseram "Não encontrei na base." em todas.
""")
st.caption(
    "Correção e fidelidade vêm de um juiz LLM (gemma3:12b) ainda não comparado com "
    f"rótulos humanos ({juiz['rotulos_preenchidos']} de "
    f"{juiz['rotulos_necessarios']} feitos). As demais métricas são código puro."
)

busca, resposta, pergunta_a_pergunta, metodo = st.tabs(
    ["Busca", "Resposta", "Por pergunta", "Método"]
)

with busca:
    st.subheader("Evolução da busca")
    st.write(
        "Cada etapa soma uma peça à anterior. A linha mostra a média geral nas 34 "
        "perguntas com artigo esperado."
    )
    evolucao = pd.DataFrame(evolucao_da_busca(registros))
    evolucao["rotulo"] = evolucao["etapa"].map(lambda e: quebrar(e, 14))
    ordem_das_etapas = [quebrar(etapa, 14) for _, etapa in EVOLUCAO]
    base = alt.Chart(evolucao).encode(
        x=alt.X(
            "rotulo:N",
            sort=ordem_das_etapas,
            title=None,
            axis=alt.Axis(labelAngle=0, labelExpr=EM_LINHAS, labelLimit=0),
        ),
        y=alt.Y("media:Q", title="Média", scale=alt.Scale(domain=[0.5, 1])),
        color=alt.Color(
            "metrica:N",
            title=None,
            scale=alt.Scale(
                domain=["Recall@5", "MRR", "Recall@1"], range=CORES_DA_EVOLUCAO
            ),
            legend=alt.Legend(orient="top"),
        ),
        tooltip=[
            alt.Tooltip("etapa:N", title="Etapa"),
            alt.Tooltip("metrica:N", title="Métrica"),
            alt.Tooltip("media:Q", title="Média", format=".2f"),
            alt.Tooltip("baixo:Q", title="IC 95% de", format=".2f"),
            alt.Tooltip("alto:Q", title="até", format=".2f"),
        ],
    )
    rotulos = base.mark_text(dy=-12, fontSize=12).encode(
        text=alt.Text("media:Q", format=".2f"), color=alt.value("gray")
    )
    st.altair_chart(
        (
            base.mark_line(strokeWidth=2)
            + base.mark_point(size=80, filled=True)
            + rotulos
        ).properties(height=340),
        width="stretch",
    )
    inicio = {r["nome"]: r for r in registros}
    primeiro, ultimo = EVOLUCAO[0][0], EVOLUCAO[-1][0]
    st.markdown(
        f"- Da densa pura à busca completa, o MRR foi de "
        f"{numero(inicio[primeiro]['metricas']['geral']['mrr']['media'])} para "
        f"{numero(inicio[ultimo]['metricas']['geral']['mrr']['media'])}: o artigo certo "
        "passou a vir mais perto do topo.\n"
        "- O **artigo citado primeiro** consertou as perguntas que citam o número do "
        "artigo; o **nome da lei no texto** ajudou sem custo na hora da pergunta; o "
        "**reranker** ajudou mais as perguntas em linguagem leiga, ao custo de uns 30 "
        "segundos em CPU."
    )

    st.subheader("Todos os experimentos de busca")
    st.write(
        "Recall@5 geral e por tipo de pergunta de cada configuração medida, da melhor "
        "para a pior. A média geral esconde onde a busca sofre; os tipos mostram onde."
    )
    tabela = pd.DataFrame(
        [
            {
                "Configuração": r["descricao"],
                "Papel": PAPEIS.get(r["nome"], ""),
                "Geral": r["metricas"]["geral"]["recall@5"]["media"],
                "IC 95%": "{} a {}".format(
                    *(numero(v) for v in r["metricas"]["geral"]["recall@5"]["ic95"])
                ),
                "MRR": r["metricas"]["geral"]["mrr"]["media"],
            }
            | {
                NOMES_DOS_TIPOS[tipo]: r["metricas"][tipo]["recall@5"]["media"]
                for tipo in ("direta", "leiga", "varios_artigos", "termo_exato")
            }
            for r in registros
        ]
    ).sort_values("Geral", ascending=False)
    barra = {"min_value": 0, "max_value": 1, "format": "%.2f", "width": "small"}
    st.dataframe(
        tabela,
        hide_index=True,
        width="stretch",
        # Todas as linhas à vista; no celular a tabela rola só na horizontal.
        height=(len(tabela) + 1) * 35 + 3,
        column_config={
            "Configuração": st.column_config.TextColumn(width="medium"),
            "Geral": st.column_config.ProgressColumn(
                help="Recall@5 nas 34 perguntas com artigo esperado.", **barra
            ),
            "MRR": st.column_config.NumberColumn(format="%.2f", width="small"),
        }
        | {
            NOMES_DOS_TIPOS[tipo]: st.column_config.ProgressColumn(**barra)
            for tipo in ("direta", "leiga", "varios_artigos", "termo_exato")
        },
    )
    st.markdown(
        "- **A híbrida (BM25 + densa) piorou** em todas as variações de peso: o texto "
        "dos artigos é longo e o BM25 premia repetição de palavra, não o artigo certo.\n"
        f"- A melhor configuração em MRR é **{melhor['descricao']}**, que é a busca "
        "Completa do app. Ela foi escolhida olhando o `dev`, então seu número é "
        "otimista até a medição no `test`.\n"
        "- **Linguagem leiga** separa as buscas: o BM25 zera, porque o leigo não usa as "
        "palavras da lei, e o reranker é o que mais ajuda.\n"
        "- **Termo exato** é onde a densa pura falha; o artigo citado primeiro conserta."
    )

with resposta:
    st.subheader("A resposta, nas duas rodadas")
    st.write(
        "Mesmo modelo (gemma3:4b) e mesmo prompt; só a busca muda. Abstenção indevida: "
        "quanto menor, melhor. As outras: quanto maior, melhor."
    )
    st.altair_chart(
        barras_com_intervalo(
            comparacao(rodadas, METRICAS_DA_RESPOSTA), "metrica", "Métrica"
        ),
        width="stretch",
    )

    st.subheader("Por tipo de pergunta")
    escolha = st.selectbox(
        "Métrica",
        [
            "abstencao_indevida",
            "correta",
            "cita_artigo",
            "citacoes_nos_trechos",
            "recall@5",
        ],
        format_func=NOMES_DAS_METRICAS.get,
    )
    por_tipo = pd.DataFrame(
        [
            {"rodada": nome} | linha
            for rodada, nome in RODADAS.items()
            for linha in linhas_de_metrica(rodadas[rodada], escolha)
            if linha["tipo"] != "Geral"
        ]
    )
    st.altair_chart(barras_com_intervalo(por_tipo, "tipo", "Tipo"), width="stretch")
    st.markdown(f"""
- **Linguagem leiga foi o tipo que mais ganhou:** correção de
  {numero(valor(baseline, "correta", "leiga")["media"])} para
  {numero(valor(completa, "correta", "leiga")["media"])}, porque o artigo certo
  passou a chegar ao modelo.
- **Vários artigos perdeu correção** ({numero(valor(baseline, "correta", "varios_artigos")["media"])}
  para {numero(valor(completa, "correta", "varios_artigos")["media"])}). Com mais
  artigos relevantes, o modelo responde, mas junta mal as partes. São 5 perguntas:
  cada uma vale 0,20.
- **Fidelidade ficou em 1,00** segundo o juiz, mas a conferência por código achou
  citações de artigos não recebidos. O juiz é mais tolerante do que a regra.
""")

with pergunta_a_pergunta:
    st.subheader("O que mudou em cada pergunta")
    rotulos_das_trocas = {
        "passou_a_correta": "Passaram a correta",
        "deixou_de_ser_correta": "Deixaram de ser correta",
        "deixou_de_se_abster": 'Deixaram de dizer "não encontrei"',
        "cita_fora_dos_trechos": "Citam artigo não recebido",
    }
    colunas = st.columns(len(rotulos_das_trocas))
    for coluna, (chave, rotulo) in zip(
        colunas, rotulos_das_trocas.items(), strict=True
    ):
        coluna.metric(rotulo, len(trocas[chave]), border=True)
        coluna.caption(", ".join(trocas[chave]) or "nenhuma")

    so_mudancas = st.toggle("Só as perguntas em que algo mudou", value=True)
    tabela = pd.DataFrame(
        [
            {
                "id": p["id"],
                "tipo": NOMES_DOS_TIPOS[p["tipo"]],
                "pergunta": p["pergunta"],
                "posição antes": posicao(p, "baseline"),
                "posição depois": posicao(p, "completa"),
                "correta antes": p["baseline_correta"],
                "correta depois": p["completa_correta"],
                "absteve antes": p["baseline_absteve"],
                "absteve depois": p["completa_absteve"],
                "cita fora": ", ".join(p["completa_fora"]),
            }
            for p in perguntas
        ]
    )
    if so_mudancas:
        mudou = (
            (tabela["correta antes"] != tabela["correta depois"])
            | (tabela["absteve antes"] != tabela["absteve depois"])
            | (tabela["posição antes"] != tabela["posição depois"])
            | (tabela["cita fora"] != "")
        )
        tabela = tabela[mudou]
    st.dataframe(
        tabela,
        hide_index=True,
        width="stretch",
        column_config={
            "pergunta": st.column_config.TextColumn(width="large"),
            "posição antes": st.column_config.TextColumn(
                help="Posição do primeiro artigo esperado entre os 5 trazidos."
            ),
            "correta antes": st.column_config.CheckboxColumn(),
            "correta depois": st.column_config.CheckboxColumn(),
            "absteve antes": st.column_config.CheckboxColumn(),
            "absteve depois": st.column_config.CheckboxColumn(),
        },
    )
    st.caption(
        "Antes: busca do baseline. Depois: busca completa do app. Correta é o veredito "
        "do juiz LLM."
    )

with metodo:
    st.subheader("Como é medido")
    st.write(
        "Um RAG erra em dois lugares: a busca não trouxe o artigo certo, ou trouxe e o "
        "modelo respondeu mal. Cada metade tem métricas próprias, para saber onde "
        "consertar."
    )
    st.dataframe(
        pd.DataFrame(
            [
                [
                    "Busca",
                    "Recall@k",
                    "O artigo esperado veio entre os k primeiros?",
                    "Código",
                ],
                [
                    "Busca",
                    "MRR",
                    "Quão perto do topo ele veio? (1 ÷ posição)",
                    "Código",
                ],
                [
                    "Resposta",
                    "Abstenção indevida",
                    'Disse "não encontrei" com a resposta no corpus?',
                    "Código",
                ],
                [
                    "Resposta",
                    "Abstenção correta",
                    'Fora do escopo, disse "não encontrei"?',
                    "Código",
                ],
                [
                    "Resposta",
                    "Cita lei e artigo",
                    "A resposta diz de onde tirou?",
                    "Código",
                ],
                [
                    "Resposta",
                    "Citações só de artigos recebidos",
                    "Algum artigo citado veio da memória do modelo?",
                    "Código",
                ],
                ["Resposta", "Correta", "Bate com a resposta esperada?", "Juiz LLM"],
                ["Resposta", "Fiel", "Cada afirmação está nos trechos?", "Juiz LLM"],
            ],
            columns=["Metade", "Métrica", "Pergunta que responde", "Como"],
        ),
        hide_index=True,
        width="stretch",
    )
    st.markdown(
        "- **Intervalos de 95% por bootstrap** em todas as médias: com 5 a 14 "
        "perguntas por tipo, uma pergunta muda o número em até 0,20.\n"
        "- **O split `test` está fechado.** As escolhas foram feitas no `dev`; o número "
        "final virá do `test`, rodado uma única vez."
    )
    st.subheader("O juiz também é testado")
    acertos = sum(acertou for _, acertou in juiz["sonda"])
    st.write(
        f"Numa sonda com respostas falsas de propósito, o gemma3:12b acertou "
        f"{acertos} de {len(juiz['sonda'])} casos. O gemma3:4b, o mesmo modelo que "
        "gera as respostas, aprovou respostas erradas e foi descartado como juiz."
    )
    st.dataframe(
        pd.DataFrame(juiz["sonda"], columns=["Caso", "Juiz acertou"]),
        hide_index=True,
        width="stretch",
    )
    st.progress(
        juiz["rotulos_preenchidos"] / juiz["rotulos_necessarios"],
        text=(
            f"Validação com rótulos humanos: {juiz['rotulos_preenchidos']} de "
            f"{juiz['rotulos_necessarios']} respostas rotuladas. A meta é 80% de "
            "concordância."
        ),
    )
