"""Lê referências a artigos em texto livre: os citados na pergunta e os citados na resposta."""

import re
import unicodedata

# Como cada lei costuma ser chamada, já sem acento e em minúsculas.
NOMES_DAS_LEIS = {
    "lgpd": ("13.709", "13709", "lgpd", "lei geral de protecao de dados"),
    "cdc": ("8.078", "8078", "cdc", "codigo de defesa do consumidor"),
    "licitacoes": ("14.133", "14133", "lei de licitacoes", "licitacoes e contratos"),
}
_CITACAO = re.compile(r"\bart(?:igo)?s?\.?\s*(\d+)\s*[ºo°]?(?:\s*-\s*([a-z])\b)?")

# Na resposta, a citação liga um artigo a uma lei, nas duas ordens em que o modelo
# escreve: "(Lei 8.078/1990, art. 49)" e "art. 51, inciso VI, da Lei 8.078/1990".
_LEI = (
    r"(lei\s*(?:n[ºo°.]*\s*)?\d{1,2}\.?\d{3}(?:/\d{4})?|lgpd|cdc"
    r"|codigo de defesa do consumidor|lei geral de protecao de dados|lei de licitacoes)"
)
_NUMERO = r"\d+\s*[ºo°]?(?:\s*-\s*[a-z]\b)?"
_NUMEROS = rf"({_NUMERO}(?:\s*(?:,|e)\s*{_NUMERO})*)"
_ART = r"\bart(?:igo)?s?\.?\s*"
_LEI_ANTES = re.compile(rf"{_LEI}\s*,?\s*{_ART}{_NUMEROS}")
_LEI_DEPOIS = re.compile(rf"{_ART}{_NUMEROS}[^.;()\n]{{0,40}}?\s+d[ao]\s+{_LEI}")
_UM_NUMERO = re.compile(r"(\d+)\s*[ºo°]?(?:\s*-\s*([a-z])\b)?")


def sem_acento(texto: str) -> str:
    """Minúsculas e sem acento, para "Licitações" e "licitacoes" serem o mesmo termo."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def _sufixo(numero: str, letra: str) -> str:
    return f"{numero}-{letra.upper()}" if letra else numero


def artigos_citados(pergunta: str, ids: set[str]) -> list[str]:
    """Ids dos artigos que a pergunta cita pelo número, como em "art. 75 da Lei 14.133".

    Se a pergunta nomeia uma ou mais leis, só elas contam; se não nomeia nenhuma,
    o número vale para as três. Devolve só ids que existem no corpus.
    """
    texto = sem_acento(pergunta)
    leis = [
        lei for lei, nomes in NOMES_DAS_LEIS.items() if any(n in texto for n in nomes)
    ]
    leis = leis or list(NOMES_DAS_LEIS)
    citados = []
    for numero, letra in _CITACAO.findall(texto):
        for lei in leis:
            artigo = f"{lei}-art-{_sufixo(numero, letra)}"
            if artigo in ids and artigo not in citados:
                citados.append(artigo)
    return citados


def _sigla(nome_da_lei: str) -> str | None:
    for sigla, nomes in NOMES_DAS_LEIS.items():
        if any(nome in nome_da_lei for nome in nomes):
            return sigla
    return None


def citacoes_da_resposta(resposta: str) -> list[str]:
    """Ids dos artigos que a resposta cita junto com a lei, na ordem em que aparecem.

    Um "art. 75" solto, sem lei ao lado, não conta: não dá para saber de qual lei é.
    Citações de leis fora do corpus também não contam; costumam ser o próprio texto
    do artigo recuperado citando outra lei ("art. 5º da Lei nº 12.846").
    """
    texto = sem_acento(resposta)
    achados = [
        (m.start(), m.group(1), m.group(2)) for m in _LEI_ANTES.finditer(texto)
    ] + [(m.start(), m.group(2), m.group(1)) for m in _LEI_DEPOIS.finditer(texto)]
    citados = []
    for _, lei, numeros in sorted(achados):
        sigla = _sigla(lei)
        if sigla is None:
            continue
        for numero, letra in _UM_NUMERO.findall(numeros):
            artigo = f"{sigla}-art-{_sufixo(numero, letra)}"
            if artigo not in citados:
                citados.append(artigo)
    return citados


def citacoes_fora_dos_trechos(resposta: str, recuperados: list[str]) -> list[str]:
    """Artigos citados na resposta que o modelo não recebeu: sinal de invenção."""
    return [c for c in citacoes_da_resposta(resposta) if c not in recuperados]
