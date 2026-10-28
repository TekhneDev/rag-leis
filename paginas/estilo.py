"""Identidade visual do app: CSS global, as orelhas de índice e o carimbo.

A página imita uma folha de código impresso (um vade mecum) sobre a mesa: capa
grafite no topo, folha branca no meio, orelhas coloridas na borda, uma cor por lei.
As cores e fontes base ficam em .streamlit/config.toml; aqui só o que o tema do
Streamlit não cobre. Os contêineres estilizados são achados pela classe
"st-key-<chave>" que o Streamlit dá a cada st.container(key=...).

Regra tipográfica: o texto da lei e os títulos em Literata, serifa de livro; a
voz do sistema (a nota, os controles) em Public Sans.
"""

import base64
from dataclasses import dataclass
from html import escape

import streamlit as st

GRAFITE = "#1C1F26"
TINTA = "#1B1D22"
CINZA = "#5B606A"
LINHA = "#DCDDE0"
MESA = "#E3E4E6"
SELO = "#0A6B4E"
ALERTA = "#8F5413"
NEUTRO = "#5F6A79"


@dataclass(frozen=True)
class Lei:
    sigla: str
    nome: str
    cor: str


# Cores das orelhas, escolhidas para texto branco passar de 7:1 sobre elas.
LEIS = {
    "Lei 13.709/2018": Lei("LGPD", "Lei Geral de Proteção de Dados", "#24507A"),
    "Lei 8.078/1990": Lei("CDC", "Código de Defesa do Consumidor", "#8A2432"),
    "Lei 14.133/2021": Lei("Licitações", "Lei de Licitações e Contratos", "#4D6630"),
}

CSS = f"""
<style>
:root {{
  --grafite: {GRAFITE}; --tinta: {TINTA}; --cinza: {CINZA}; --linha: {LINHA};
  --mesa: {MESA}; --selo: {SELO}; --alerta: {ALERTA};
  --serif: "Literata", Georgia, serif;
  --folha: 1000px;
}}

/* Capa: cabeçalho grafite com a navegação. */
header[data-testid="stHeader"] {{ background: var(--grafite); }}
header [data-testid="stTopNavLink"] {{ background: transparent; border-radius: 0; }}
header [data-testid="stTopNavLink"] p {{ color: #B9BEC6; font-size: 0.92rem; }}
header [data-testid="stTopNavLink"]:hover p,
header [data-testid="stTopNavLink"][aria-current="page"] p {{ color: #fff; }}
header [data-testid="stTopNavLink"][aria-current="page"] {{ box-shadow: inset 0 -2px 0 #fff; }}
header [data-testid="stExpandSidebarButton"] {{ color: #fff; }}
[data-testid="stDecoration"] {{ display: none; }}

/* Mesa e folha. */
[data-testid="stAppViewContainer"] {{ background: var(--mesa); }}
.block-container {{
  max-width: var(--folha); background: #fff; margin: 5.25rem auto 3rem;
  padding: 2.75rem 3.5rem 3rem; border-radius: 2px;
  box-shadow: 0 1px 2px rgba(0,0,0,.06), 0 24px 48px -28px rgba(0,0,0,.35);
}}
@media (max-width: 1080px) {{
  .block-container {{ margin: 3.75rem 0 0; padding: 1.75rem 1.25rem 2.5rem; box-shadow: none; max-width: none; }}
}}

/* Cabeça de página corrida, como no alto de cada folha de um código. */
.cabeca {{
  display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 0.25rem 1rem;
  font: 500 0.74rem/1.3 var(--serif); letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--cinza); padding-bottom: 0.45rem; margin-bottom: 1.6rem;
  border-bottom: 3px double var(--linha);
}}
.cabeca .leis span + span::before {{ content: " · "; color: var(--cinza); }}
.cabeca .leis b {{ font-weight: 600; }}
.titulo h1 {{
  font: 600 clamp(1.6rem, 1.2rem + 1.6vw, 2.3rem)/1.15 var(--serif); letter-spacing: -0.01em;
  margin: 0 0 0.5rem; padding: 0;
}}
.titulo p {{ color: var(--cinza); font-size: 1rem; line-height: 1.6; max-width: 60ch; margin: 0 0 1.4rem; }}

h2.secao {{
  font: 600 1.05rem/1.3 var(--serif); margin: 0 0 0.6rem; padding: 0;
}}
h2.secao small {{ font: 400 0.85rem var(--serif); font-style: italic; color: var(--cinza); margin-left: 0.4rem; }}

/* Campo da pergunta. */
.st-key-caixa {{ border: 1px solid #C4C7CC; border-radius: 4px; padding: 0.7rem 0.85rem 0.6rem; background: #fff; }}
.st-key-caixa:focus-within {{ border-color: var(--grafite); box-shadow: 0 0 0 3px rgba(28,31,38,.12); }}
.st-key-caixa [data-testid="stForm"] {{ border: 0; padding: 0; }}
.st-key-caixa [data-testid="stTextAreaRootElement"] {{ border: 0; background: transparent; }}
.st-key-caixa textarea {{ font-size: 1.0625rem; line-height: 1.55; background: transparent; resize: none; padding-left: 0.1rem; }}
.st-key-caixa textarea:focus-visible {{ outline: none !important; }}
.st-key-caixa [data-testid="InputInstructions"] {{ display: none; }}
.st-key-linha-ajustes {{ flex-wrap: wrap; row-gap: 0.25rem; }}
.aviso {{ font-size: 0.84rem; color: var(--cinza); margin: 0; }}

/* Sumário de consultas frequentes, com pontilhado até a sigla da lei. */
.st-key-sumario {{ margin-top: 2.2rem; gap: 0; }}
.st-key-sumario button {{
  justify-content: flex-start; text-align: left; min-height: 46px; padding: 0.55rem 0;
  border-radius: 0; color: var(--tinta);
}}
.st-key-sumario button > div, .st-key-sumario button > div > span,
.st-key-sumario button [data-testid="stMarkdownContainer"] {{ justify-content: flex-start; width: 100%; }}
.st-key-sumario button p {{
  display: flex; align-items: baseline; width: 100%; text-align: left;
  font: 400 1.02rem/1.45 var(--serif);
}}
.st-key-sumario button p > span {{
  flex: 1 0 4.5rem; display: flex; align-items: baseline; white-space: nowrap;
  font: 600 0.72rem var(--serif); letter-spacing: 0.1em; text-transform: uppercase;
}}
.st-key-sumario button p > span::before {{
  content: ""; flex: 1; border-bottom: 1px dotted #A3A7AE; margin: 0 0.6rem 0.25rem;
}}
.st-key-sumario button:hover p {{ text-decoration: underline; text-underline-offset: 3px; }}

/* Colofão no pé da folha. */
.st-key-colofao {{ margin-top: 2.5rem; padding-top: 0.9rem; border-top: 1px solid var(--linha); gap: 0.3rem; }}
.colofao {{ font: 400 0.86rem/1.6 var(--serif); font-style: italic; color: var(--cinza); max-width: 72ch; margin: 0; }}
.st-key-colofao [data-testid="stPageLink"] a {{ padding-left: 0; }}

/* Nota: a resposta, com filete grafite, e a margem com o carimbo. */
.st-key-nota {{ border-left: 3px solid var(--grafite); padding-left: 1.1rem; }}
.st-key-nota [data-testid="stMarkdownContainer"] p,
.st-key-nota [data-testid="stMarkdownContainer"] li {{ font-size: 1.0625rem; line-height: 1.7; max-width: 66ch; }}
.citacoes {{ display: flex; flex-wrap: wrap; gap: 0.4rem; }}
.citacao {{
  font: 600 0.76rem/1 var(--serif); letter-spacing: 0.06em; padding: 0.35rem 0.5rem 0.3rem;
  border-radius: 2px; color: #fff; background: var(--cor, var(--grafite));
}}
.citacao.fora {{ background: #fff; color: var(--alerta); box-shadow: inset 0 0 0 1px var(--alerta); }}
.st-key-margem {{ gap: 0.6rem; }}
.st-key-margem p {{ font-size: 0.86rem; line-height: 1.5; color: var(--cinza); margin: 0; }}
.st-key-margem p b {{ color: var(--tinta); font-weight: 600; }}
.carimbo {{ width: 92px; height: 92px; }}
@media (prefers-reduced-motion: no-preference) {{
  .carimbo {{ animation: carimbar .28s ease-out both; }}
  @keyframes carimbar {{ from {{ opacity: 0; transform: scale(1.25); }} to {{ opacity: 1; transform: scale(1); }} }}
}}

/* O artigo composto como num código impresso. */
.folha-lei {{ margin-top: 2.2rem; }}
.cabeca-lei {{
  display: flex; align-items: center; gap: 0.7rem; flex-wrap: wrap;
  padding-bottom: 0.5rem; border-bottom: 1px solid var(--linha); margin-bottom: 1rem;
}}
.aba {{
  font: 600 0.72rem/1 var(--serif); letter-spacing: 0.1em; text-transform: uppercase;
  color: #fff; background: var(--cor); padding: 0.4rem 0.55rem 0.35rem; border-radius: 2px;
}}
.cabeca-lei .nome {{ font: 600 0.95rem var(--serif); }}
.cabeca-lei .num {{ font: 400 0.88rem var(--serif); color: var(--cinza); margin-left: auto; }}
.corpo-lei {{ display: grid; grid-template-columns: minmax(0, 1fr) 13rem; gap: 2.2rem; }}
@media (max-width: 760px) {{ .corpo-lei {{ grid-template-columns: 1fr; gap: 1rem; }} }}
.lei {{ font: 400 1.02rem/1.68 var(--serif); color: var(--tinta); hyphens: auto; -webkit-hyphens: auto; }}
.lei p {{ margin: 0 0 0.45rem; text-align: justify; overflow-wrap: break-word; }}
@media (max-width: 760px) {{ .lei p {{ text-align: left; }} }}
.lei .mk {{ font-weight: 600; }}
.lei .caput .mk {{ font-weight: 700; }}
.lei .paragrafo {{ text-indent: 1.6em; }}
.lei .inciso {{ padding-left: 2.2em; text-indent: -1.4em; }}
.lei .alinea {{ padding-left: 3.6em; text-indent: -1.4em; }}
.lei .item {{ padding-left: 5em; text-indent: -1.4em; }}
.lei .pena {{ padding-left: 1.6em; }}
.lei .nota-red {{ font-size: 0.8em; font-style: italic; color: var(--cinza); }}
.margem-lei {{ font: 400 0.84rem/1.5 var(--serif); color: var(--cinza); border-left: 1px solid var(--linha); padding-left: 1rem; }}
.margem-lei p {{ margin: 0 0 0.7rem; }}
.margem-lei .citado {{ font-style: italic; color: var(--tinta); }}
.margem-lei a {{ color: var(--tinta); }}
@media (max-width: 760px) {{ .margem-lei {{ border-left: 0; padding-left: 0; border-top: 1px solid var(--linha); padding-top: 0.7rem; }} }}

/* Remissões: os outros artigos trazidos pela busca. */
.remissoes {{ margin-top: 2.4rem; }}
.remissoes details {{ border-top: 1px solid var(--linha); }}
.remissoes details:last-child {{ border-bottom: 1px solid var(--linha); }}
.remissoes summary {{
  list-style: none; cursor: pointer; min-height: 46px; padding: 0.7rem 2rem 0.7rem 0; position: relative;
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.2rem 0.7rem;
}}
.remissoes summary::-webkit-details-marker {{ display: none; }}
.remissoes summary::after {{ content: "+"; position: absolute; right: 0.3rem; top: 0.7rem; color: var(--cinza); font-size: 1.1rem; }}
.remissoes details[open] summary::after {{ content: "–"; }}
.remissoes summary:focus-visible {{ outline: 2px solid var(--grafite); outline-offset: 2px; }}
.remissoes .ref {{ font: 600 1rem var(--serif); }}
.remissoes .onde {{ flex: 1 1 18rem; font-size: 0.86rem; color: var(--cinza);
  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
.remissoes .lei {{ max-height: 24rem; overflow-y: auto; padding: 0.2rem 0.4rem 0.6rem 0; }}
.remissoes .lei + p a {{ font-size: 0.86rem; color: var(--tinta); }}
.remissoes .lei + p {{ margin: 0 0 1rem; }}

/* Orelhas de índice na borda direita da folha; somem quando a folha ocupa a tela. */
.orelhas {{ position: fixed; top: 8.5rem; left: calc(50% + var(--folha) / 2); display: flex; flex-direction: column; gap: 4px; z-index: 5; }}
.orelhas span {{
  writing-mode: vertical-rl; font: 600 0.7rem/1 var(--serif); letter-spacing: 0.12em; text-transform: uppercase;
  color: #fff; background: var(--cor); padding: 0.9rem 0.5rem; border-radius: 0 3px 3px 0;
  width: 1.9rem; box-sizing: border-box; opacity: .38; transition: opacity .2s, width .2s;
}}
.orelhas span.ativa {{ opacity: 1; width: 2.35rem; }}
@media (max-width: 1080px) {{ .orelhas {{ display: none; }} }}

/* Alvos de toque e foco. */
button[data-testid^="stBaseButton"], [data-testid="stPopoverButton"] {{ min-height: 44px; }}
[data-testid="stExpandSidebarButton"] {{ min-width: 44px; min-height: 44px; }}
button[data-testid="stBaseButton-primaryFormSubmit"] {{ font-weight: 600; padding: 0 1.5rem; letter-spacing: 0.01em; }}
:focus-visible {{ outline: 2px solid var(--grafite) !important; outline-offset: 2px; }}
@media (max-width: 640px) {{ [data-testid="stPopoverBody"] {{ width: calc(100vw - 2rem) !important; max-width: none; }} }}
</style>
"""


def aplicar() -> None:
    st.html(CSS)


def cabeca(titulo: str, subtitulo: str) -> None:
    """Cabeça de página corrida (as três leis e a data da edição) e o título."""
    leis = "".join(
        f'<span><b style="color:{lei.cor}">{lei.sigla}</b></span>'
        for lei in LEIS.values()
    )
    st.html(f"""
<div class="cabeca"><span class="leis">{leis}</span><span>Atualizado até 9.10.2026</span></div>
<div class="titulo"><h1>{titulo}</h1><p>{subtitulo}</p></div>""")


def orelhas(ativas: set[str] | None = None) -> None:
    """As abas coloridas na borda da folha. Sem `ativas`, todas acesas."""
    abas = "".join(
        f'<span class="{"ativa" if ativas is None or nome in ativas else ""}" '
        f'style="--cor:{lei.cor}">{lei.sigla}</span>'
        for nome, lei in LEIS.items()
    )
    st.html(f'<nav class="orelhas" aria-hidden="true">{abas}</nav>')


# Estado da conferência -> (texto em volta do carimbo, cor, símbolo do centro, descrição).
CARIMBOS = {
    "conferido": ("CONFERIDO · CITAÇÃO NA BASE · ", SELO, "✓", "Citações conferidas"),
    "atencao": ("CONFERIR · CITAÇÃO FORA · ", ALERTA, "!", "Conferir citação"),
    "sem_citacao": ("SEM CITAÇÃO · VER FONTES · ", NEUTRO, "?", "Resposta sem citação"),
    "fora_da_base": ("FORA DA BASE · SEM RESPOSTA · ", NEUTRO, "–", "Fora da base"),
}


def carimbo(estado: str) -> str:
    """Carimbo redondo com o texto pela borda e a tinta falhando um pouco, como um
    carimbo de borracha de verdade. Vai como <img>, porque o st.html remove <svg>."""
    texto, cor, simbolo, descricao = CARIMBOS[estado]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"
  font-family="'IBM Plex Mono', 'DejaVu Sans Mono', Menlo, monospace">
  <defs>
    <path id="volta" d="M50,50 m-36,0 a36,36 0 1,1 72,0 a36,36 0 1,1 -72,0"/>
    <filter id="tinta" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency="1.4" numOctaves="1" seed="{len(estado)}"/>
      <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -0.9 1.3"/>
      <feComposite in="SourceGraphic" operator="in"/>
    </filter>
  </defs>
  <g filter="url(#tinta)" transform="rotate(-8 50 50)" fill="{cor}" stroke="{cor}">
    <circle cx="50" cy="50" r="46" fill="none" stroke-width="3.4"/>
    <circle cx="50" cy="50" r="27" fill="none" stroke-width="1.8"/>
    <text font-size="9" font-weight="600" letter-spacing="0.8" stroke="none">
      <textPath href="#volta" textLength="222">{texto}</textPath>
    </text>
    <text x="50" y="59" text-anchor="middle" font-size="27" font-weight="700" stroke="none">{simbolo}</text>
  </g>
</svg>"""
    dados = base64.b64encode(svg.encode()).decode()
    return (
        f'<img class="carimbo" src="data:image/svg+xml;base64,{dados}" '
        f'alt="Carimbo: {escape(descricao)}">'
    )
