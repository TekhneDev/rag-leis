"""Interface web do rag-leis. Uso: streamlit run app.py"""

import streamlit as st

from rag_leis.generate import NAO_ENCONTREI, generate
from rag_leis.index import APELIDOS, carregar_corpus
from rag_leis.ingest import LEIS
from rag_leis.retrieve import PADRAO, artigos_citados, montar_pipeline

# As duas configurações vêm da tabela de experimentos (results/experimentos/tabela.md).
BUSCAS = {
    "Rápida": PADRAO | {"busca": "densa", "cabecalho": True, "referencia": True},
    "Completa, com reranker": PADRAO
    | {
        "busca": "densa",
        "cabecalho": True,
        "referencia": True,
        "reranker": "BAAI/bge-reranker-v2-m3",
    },
}
DESCRICAO = {
    "Rápida": "Busca por significado, com o nome da lei no texto indexado e o artigo "
    "citado pelo número na frente.",
    "Completa, com reranker": "A rápida, mais um reranker que relê os 20 primeiros. "
    "Acerta mais em perguntas em linguagem leiga, mas soma uns 30 segundos em CPU.",
}
# Perguntas de exemplo que não estão no conjunto ouro, para não misturar demo e gabarito.
EXEMPLOS = [
    "Comprei um celular pelo site e me arrependi. Tenho quanto tempo para devolver?",
    "Uma empresa pode compartilhar meus dados com parceiros sem me avisar?",
    "O que diz o art. 6º da Lei 8.078/1990?",
    "Qual é a pena para quem dirige embriagado?",
]
URL_DA_LEI = {lei.nome: lei.url for lei in LEIS}


@st.cache_resource(show_spinner="Carregando os modelos de busca...")
def pipeline(nome: str):
    return montar_pipeline(BUSCAS[nome])


@st.cache_resource
def artigos() -> dict[str, dict]:
    return {registro["id"]: registro for registro in carregar_corpus()}


def mostrar_artigo(posicao: int, artigo: dict, citados: list[str]) -> None:
    rotulo = f"{posicao}. {artigo['lei']}, art. {artigo['artigo']}"
    if artigo["id"] in citados:
        rotulo += " · citado na pergunta"
    with st.expander(rotulo, expanded=posicao == 1):
        st.caption(
            " · ".join(
                p
                for p in (APELIDOS[artigo["lei"]], artigo["titulo"], artigo["capitulo"])
                if p
            )
        )
        st.text(artigo["texto"])
        st.markdown(f"[Texto completo da lei no Planalto]({URL_DA_LEI[artigo['lei']]})")


st.set_page_config(page_title="rag-leis", page_icon="⚖️", layout="wide")
st.title("rag-leis")
st.write(
    "Perguntas sobre a LGPD, o Código de Defesa do Consumidor e a Lei de Licitações, "
    "respondidas só com base nos artigos encontrados, com a fonte citada."
)
st.warning("Este sistema é um estudo e não substitui orientação jurídica.")

with st.sidebar:
    st.header("Configuração")
    nome_busca = st.radio("Busca", list(BUSCAS), key="busca")
    st.caption(DESCRICAO[nome_busca])
    gerar = st.toggle(
        "Gerar resposta com o LLM",
        value=True,
        key="gerar",
        help="Precisa do Ollama no ar (ollama serve). Sem ele, o app só mostra os artigos.",
    )
    st.caption("Em CPU, a resposta leva de 1 a 2 minutos.")
    st.divider()
    st.caption(
        "Embedding BAAI/bge-m3 · índice FAISS · LLM gemma3:4b no Ollama, local, "
        "temperatura zero. Corpus: 406 artigos baixados do Planalto em 9/10/2026."
    )

st.write("Exemplos:")
colunas = st.columns(len(EXEMPLOS))
for coluna, exemplo in zip(colunas, EXEMPLOS, strict=True):
    if coluna.button(exemplo, width="stretch"):
        st.session_state["pergunta"] = exemplo

with st.form("perguntar"):
    pergunta = st.text_area("Sua pergunta", key="pergunta", height=80)
    enviar = st.form_submit_button("Perguntar", type="primary")

if enviar and pergunta.strip():
    with st.spinner("Buscando os artigos..."):
        ids = pipeline(nome_busca)(pergunta)
    encontrados = [artigos()[i] for i in ids]
    citados = artigos_citados(pergunta, set(artigos()))

    esquerda, direita = st.columns([3, 2], gap="large")
    with direita:
        st.subheader("Artigos usados")
        for posicao, artigo in enumerate(encontrados, start=1):
            mostrar_artigo(posicao, artigo, citados)
    with esquerda:
        st.subheader("Resposta")
        if not gerar:
            st.info(
                "Geração desligada. Os artigos ao lado são os que o modelo receberia."
            )
        else:
            try:
                with st.spinner("O modelo está lendo os artigos..."):
                    resposta = generate(pergunta, encontrados)
            except RuntimeError as erro:
                st.error(f"{erro}. Se preferir, desligue a geração na barra lateral.")
            else:
                if resposta.startswith(NAO_ENCONTREI):
                    st.info(
                        "O sistema não encontrou a resposta nos artigos recuperados. "
                        "Pode ser um assunto fora das três leis."
                    )
                st.markdown(resposta)
elif enviar:
    st.error("Escreva uma pergunta antes de enviar.")
