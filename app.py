"""Interface web do rag-leis. Uso: streamlit run app.py"""

from pathlib import Path

import streamlit as st

from paginas import estilo

st.set_page_config(
    page_title="rag-leis · consulta à lei com a fonte citada",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.logo(str(Path(__file__).parent / "paginas" / "marca.svg"), size="large")
estilo.aplicar()
st.navigation(
    [
        st.Page("paginas/perguntar.py", title="Consultar", default=True),
        st.Page("paginas/avaliacao.py", title="Qualidade medida"),
    ],
    position="top",
).run()
