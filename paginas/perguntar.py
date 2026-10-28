"""Página de perguntas do app: busca, resposta e conferência das citações.

A página se lê como uma folha de código comentado: a nota (a resposta do
sistema) com o carimbo na margem, o artigo citado composto como no código
impresso e, embaixo, as remissões aos outros artigos que a busca trouxe.
"""

from html import escape

import streamlit as st

from paginas.composicao import compor
from paginas.estilo import LEIS, cabeca, carimbo, orelhas
from rag_leis.citacoes import artigos_citados, citacoes_da_resposta
from rag_leis.dados import artigos_por_id
from rag_leis.generate import MODELO_LLM, NAO_ENCONTREI, gerar_em_partes
from rag_leis.index import MODELO_EMBEDDING
from rag_leis.ingest import LEIS as FONTES
from rag_leis.painel import metricas_da_rodada
from rag_leis.retrieve import MODOS, montar_pipeline

# Nome que aparece nos ajustes e a explicação de cada modo de busca.
OPCOES = {
    "rapida": (
        "Rápida",
        "Busca por significado, com o artigo citado pelo número na frente.",
    ),
    "completa": (
        "Precisa",
        (
            "A rápida, mais uma releitura dos 20 melhores trechos. Acerta mais em "
            "perguntas em linguagem do dia a dia; soma uns 30 segundos."
        ),
    ),
}
# Perguntas de exemplo que não estão no conjunto ouro, para não misturar demo e gabarito.
# Cada uma vem com a lei onde está a resposta ("—" quando não está em nenhuma).
EXEMPLOS = [
    (
        "CDC",
        "Comprei um celular pelo site e me arrependi. Tenho quanto tempo para devolver?",
    ),
    ("LGPD", "Uma empresa pode compartilhar meus dados com parceiros sem me avisar?"),
    ("CDC", "O que diz o art. 6º da Lei 8.078/1990?"),
    ("Fora da base", "Qual é a pena para quem dirige embriagado?"),
]
URL_DA_LEI = {lei.nome: lei.url for lei in FONTES}
# Cor da sigla no sumário: o tema define "red" e "blue" como as cores das orelhas.
COR_NO_SUMARIO = {"CDC": "red", "LGPD": "blue"}


@st.cache_resource(show_spinner="Preparando a busca...")
def pipeline(modo: str):
    return montar_pipeline(MODOS[modo])


@st.cache_resource
def artigos() -> dict[str, dict]:
    return artigos_por_id()


@st.cache_data
def desempenho() -> dict:
    return metricas_da_rodada("completa")["geral"]


def _nome_do_artigo(id_artigo: str) -> str:
    artigo = artigos().get(id_artigo)
    if artigo is None:
        sigla, numero = id_artigo.split("-art-")
        return f"art. {numero} ({sigla.upper()})"
    return f"{LEIS[artigo['lei']].sigla}, art. {artigo['artigo']}"


def _onde(artigo: dict) -> str:
    return " · ".join(p for p in (artigo["titulo"], artigo["capitulo"]) if p)


def _link(artigo: dict) -> str:
    return (
        f'<a href="{URL_DA_LEI[artigo["lei"]]}" target="_blank" rel="noopener">'
        f"{artigo['lei']} no site do Planalto ↗</a>"
    )


def html_do_artigo(artigo: dict, citado: bool) -> str:
    """O artigo principal, composto como no código, com a margem ao lado."""
    lei = LEIS[artigo["lei"]]
    nota = '<p class="citado">Citado na nota.</p>' if citado else ""
    return f"""
<section class="folha-lei" style="--cor:{lei.cor}">
  <div class="cabeca-lei"><span class="aba">{lei.sigla}</span>
    <span class="nome">{lei.nome}</span><span class="num">{artigo['lei']}</span></div>
  <div class="corpo-lei">
    <div class="lei" lang="pt-BR">{compor(artigo['texto'])}</div>
    <aside class="margem-lei">{nota}<p>{escape(_onde(artigo))}</p><p>{_link(artigo)}</p></aside>
  </div>
</section>"""


def html_das_remissoes(artigos_: list[dict], titulo: str, nota: str = "") -> str:
    """Os outros artigos trazidos pela busca, fechados, cada um abre no lugar."""
    itens = "".join(f"""
<details style="--cor:{LEIS[a['lei']].cor}">
  <summary><span class="aba">{LEIS[a['lei']].sigla}</span>
    <span class="ref">Art. {escape(a['artigo'])}</span><span class="onde">{escape(_onde(a))}</span></summary>
  <div class="lei" lang="pt-BR">{compor(a['texto'])}</div><p>{_link(a)}</p>
</details>""" for a in artigos_)
    pequeno = f"<small>{nota}</small>" if nota else ""
    return f'<section class="remissoes"><h2 class="secao">{titulo}{pequeno}</h2>{itens}</section>'


def mostrar_folha(
    encontrados: list[dict], principal: str | None, citados: set[str]
) -> None:
    """O artigo principal composto e as remissões. Sem principal, só remissões."""
    if principal is None:
        st.html(
            html_das_remissoes(
                encontrados, "Artigos mais próximos", "nenhum responde à pergunta"
            )
        )
        return
    resto = [a for a in encontrados if a["id"] != principal]
    st.html(
        html_do_artigo(artigos()[principal], principal in citados)
        + html_das_remissoes(
            resto, "Remissões", f"outros {len(resto)} artigos consultados"
        )
    )


def conferir(resposta: str, ids: list[str]) -> tuple[str, list[str], list[str]]:
    """Estado do carimbo, citações da resposta e as citadas que não estavam nas fontes."""
    citados = citacoes_da_resposta(resposta)
    fora = [c for c in citados if c not in ids]
    if resposta.strip().startswith(NAO_ENCONTREI):
        return "fora_da_base", citados, fora
    if not citados:
        return "sem_citacao", citados, fora
    return ("atencao" if fora else "conferido"), citados, fora


def texto_da_conferencia(estado: str, citados: list[str], fora: list[str]) -> str:
    if estado == "fora_da_base":
        return (
            "<b>Fora da base.</b> O sistema consulta só a LGPD, o CDC e a Lei de "
            "Licitações e, quando a resposta não está nelas, diz isso em vez de arriscar."
        )
    if estado == "sem_citacao":
        return (
            "<b>A nota não indicou artigo.</b> Antes de usar, confira o texto dos "
            "artigos consultados abaixo."
        )
    if estado == "atencao":
        return (
            f"<b>Confira {', '.join(_nome_do_artigo(c) for c in fora)}.</b> Não estava "
            "entre os artigos consultados; essa parte pode ter vindo da memória do "
            "modelo, não da base."
        )
    if len(citados) == 1:
        return "<b>Citação conferida.</b> O artigo citado está entre os consultados."
    return (
        f"<b>{len(citados)} citações conferidas.</b> Todas estão entre os consultados."
    )


def chips(citados: list[str], fora: list[str]) -> str:
    itens = []
    for c in citados:
        artigo = artigos().get(c)
        cor = f' style="--cor:{LEIS[artigo["lei"]].cor}"' if artigo else ""
        classe = "citacao fora" if c in fora else "citacao"
        itens.append(f'<span class="{classe}"{cor}>{_nome_do_artigo(c)}</span>')
    return f'<div class="citacoes">{"".join(itens)}</div>'


def _usar_exemplo(exemplo: str) -> None:
    st.session_state["pergunta"] = exemplo
    st.session_state["exemplo_escolhido"] = True


def _juntar(primeira: str, resto):
    yield primeira
    yield from resto


cabeca(
    "Consulta à legislação",
    f"Escreva a dúvida como ela chegou. A nota sai dos {len(artigos())} artigos das "
    "três leis e aponta o artigo de onde veio, com o texto integral logo abaixo.",
)

if "busca" not in st.session_state:
    st.session_state["busca"] = "rapida"
    st.session_state["gerar"] = True

with st.container(key="caixa"), st.form("perguntar", border=False):
    pergunta = st.text_area(
        "Sua pergunta",
        key="pergunta",
        height=104,
        label_visibility="collapsed",
        placeholder="Ex.: Um cliente comprou pelo site e quer devolver. Qual é o prazo?",
    )
    esquerda, direita = st.columns([4, 1], vertical_alignment="center")
    esquerda.caption(
        f"Busca {OPCOES[st.session_state['busca']][0].lower()}"
        + (
            " · nota em 1 a 2 minutos"
            if st.session_state["gerar"]
            else " · só os artigos, sem nota escrita"
        )
    )
    enviar = direita.form_submit_button("Consultar", type="primary", width="stretch")

with st.container(
    key="linha-ajustes", horizontal=True, vertical_alignment="center", gap="medium"
):
    with st.popover("Ajustes"):
        modo = st.radio(
            "Modo de busca",
            list(OPCOES),
            format_func=lambda m: OPCOES[m][0],
            key="busca",
            horizontal=True,
        )
        st.caption(OPCOES[modo][1])
        gerar = st.toggle(
            "Escrever a nota",
            key="gerar",
            help="Desligado, o app mostra só os artigos. Serve para usar sem o Ollama.",
        )
        st.caption("Num computador sem placa de vídeo, a nota leva de 1 a 2 minutos.")
        st.divider()
        st.caption(
            f"Busca {MODELO_EMBEDDING} · redação {MODELO_LLM} via Ollama, temperatura "
            f"zero · {len(artigos())} artigos baixados do Planalto em 9/10/2026."
        )
    st.html('<p class="aviso">Apoio à consulta. Não substitui orientação jurídica.</p>')
enviar = enviar or st.session_state.pop("exemplo_escolhido", False)

if enviar and pergunta.strip():
    with st.spinner(f"Procurando nos {len(artigos())} artigos..."):
        ids = pipeline(modo)(pergunta)
    encontrados = [artigos()[i] for i in ids]
    na_pergunta = artigos_citados(pergunta, set(artigos()))
    orelhas({a["lei"] for a in encontrados})

    st.write("")
    texto, margem = st.columns([7, 3], gap="large")
    folha = st.empty()
    if not gerar:
        with texto, st.container(key="nota"):
            st.html('<h2 class="secao">Nota</h2>')
            st.info(
                "A nota escrita está desligada nos ajustes. Abaixo, os artigos consultados."
            )
        with folha.container():
            mostrar_folha(encontrados, ids[0], set(na_pergunta))
    else:
        with folha.container():
            mostrar_folha(encontrados, ids[0], set(na_pergunta))
        with texto, st.container(key="nota"):
            st.html('<h2 class="secao">Nota</h2>')
            try:
                with st.spinner(
                    f"Lendo {len(encontrados)} artigos e escrevendo a nota. "
                    "Costuma levar de 1 a 2 minutos."
                ):
                    partes = gerar_em_partes(pergunta, encontrados)
                    primeira = next(partes, "")
                resposta = st.write_stream(_juntar(primeira, partes))
            except RuntimeError as erro:
                st.error(
                    f"{erro}. Para ver só os artigos enquanto isso, desligue "
                    '"Escrever a nota" em Ajustes.'
                )
                resposta = None
            if resposta is not None:
                estado, citados, fora = conferir(resposta, ids)
                if citados:
                    st.html(chips(citados, fora))
        if resposta is not None:
            with margem, st.container(key="margem"):
                st.html(
                    carimbo(estado)
                    + f"<p>{texto_da_conferencia(estado, citados, fora)}</p>"
                )
            usados = [c for c in citados if c in ids]
            principal = None if estado == "fora_da_base" else (usados or ids)[0]
            with folha.container():
                mostrar_folha(encontrados, principal, set(usados))
elif enviar:
    st.error("A pergunta está em branco. Escreva a dúvida e clique em Consultar.")
else:
    orelhas()
    with st.container(key="sumario"):
        st.html('<h2 class="secao">Consultas frequentes</h2>')
        for i, (lei, exemplo) in enumerate(EXEMPLOS):
            st.button(
                f"{exemplo} :{COR_NO_SUMARIO.get(lei, 'gray')}[{lei}]",
                key=f"exemplo-{i}",
                type="tertiary",
                width="stretch",
                on_click=_usar_exemplo,
                args=(exemplo,),
            )
    recall = round(desempenho()["recall@5"]["media"] * 100)
    with st.container(key="colofao"):
        st.html(
            '<p class="colofao">Texto das leis conforme o site do Planalto em 9 de '
            "outubro de 2026, sem os trechos revogados. Processamento local: a "
            "consulta não sai desta máquina. Nas perguntas de teste, o modo Precisa "
            f"trouxe {recall}% dos artigos esperados entre os 5 consultados.</p>"
        )
        st.page_link("paginas/avaliacao.py", label="Como medimos a qualidade →")
