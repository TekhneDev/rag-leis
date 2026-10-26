"""Monta o prompt com os artigos recuperados e pede a resposta a um LLM local (Ollama)."""

import json
import os
from collections.abc import Iterator

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODELO_LLM = os.environ.get("RAG_LEIS_LLM", "gemma3:4b")
NAO_ENCONTREI = "Não encontrei na base."
# Artigos muito longos são cortados para o prompt caber na janela do modelo.
MAX_CARACTERES_POR_ARTIGO = 6000
JANELA_DE_CONTEXTO = 16384

INSTRUCOES = f"""Você responde perguntas sobre legislação brasileira usando apenas os trechos de lei fornecidos.

Regras:
1. Use somente as informações dos trechos. Não use conhecimento próprio.
2. Cite a lei e o artigo em que cada afirmação se apoia, por exemplo: (Lei 8.078/1990, art. 49).
3. Se os trechos não respondem à pergunta, responda exatamente: {NAO_ENCONTREI}
4. Responda em português, de forma direta, em poucas frases."""


def montar_prompt(pergunta: str, artigos: list[dict]) -> str:
    trechos = []
    for artigo in artigos:
        texto = artigo["texto"]
        if len(texto) > MAX_CARACTERES_POR_ARTIGO:
            texto = texto[:MAX_CARACTERES_POR_ARTIGO] + "\n[trecho cortado]"
        trechos.append(f"[{artigo['lei']}, art. {artigo['artigo']}]\n{texto}")
    return "Trechos:\n\n" + "\n\n".join(trechos) + f"\n\nPergunta: {pergunta}"


def _post(corpo: dict, stream: bool = False) -> requests.Response:
    """Chama o Ollama e troca os erros comuns por mensagens que dizem o que fazer."""
    try:
        resposta = requests.post(
            f"{OLLAMA_URL}/api/chat", json=corpo, timeout=1800, stream=stream
        )
    except requests.ConnectionError as erro:
        raise RuntimeError(
            f"Ollama não respondeu em {OLLAMA_URL}. Inicie com: ollama serve"
        ) from erro
    if resposta.status_code == 404:
        raise RuntimeError(
            f"O modelo {corpo['model']} não está no Ollama. "
            f"Baixe com: ollama pull {corpo['model']}"
        )
    resposta.raise_for_status()
    return resposta


def _corpo(
    sistema: str, usuario: str, modelo: str, formato_json: bool, descarregar: bool
) -> dict:
    corpo = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
        "stream": False,
        # Temperatura zero e semente fixa para a mesma entrada dar a mesma saída.
        "options": {"temperature": 0, "seed": 42, "num_ctx": JANELA_DE_CONTEXTO},
    }
    if formato_json:
        corpo["format"] = "json"
    if descarregar:
        # O servidor guarda cerca de 1 GB por conversa anterior; com um modelo grande
        # isso enche a memória em poucas perguntas. Descarregar a cada chamada evita.
        corpo["keep_alive"] = 0
    return corpo


def conversar(
    sistema: str,
    usuario: str,
    modelo: str = MODELO_LLM,
    formato_json: bool = False,
    descarregar: bool = False,
) -> str:
    """Envia uma conversa ao Ollama e devolve o texto da resposta."""
    corpo = _corpo(sistema, usuario, modelo, formato_json, descarregar)
    return _post(corpo).json()["message"]["content"].strip()


def conversar_em_partes(
    sistema: str, usuario: str, modelo: str = MODELO_LLM
) -> Iterator[str]:
    """Como conversar, mas devolve o texto aos pedaços, à medida que o modelo escreve."""
    corpo = _corpo(sistema, usuario, modelo, formato_json=False, descarregar=False)
    corpo["stream"] = True
    with _post(corpo, stream=True) as resposta:
        for linha in resposta.iter_lines():
            if not linha:
                continue
            parte = json.loads(linha)
            yield parte.get("message", {}).get("content", "")
            if parte.get("done"):
                return


def generate(pergunta: str, artigos: list[dict]) -> str:
    """Responde à pergunta com base nos artigos, ou diz que não encontrou."""
    return conversar(INSTRUCOES, montar_prompt(pergunta, artigos))


def gerar_em_partes(pergunta: str, artigos: list[dict]) -> Iterator[str]:
    """A mesma resposta de generate, aos pedaços, para a interface mostrar enquanto sai."""
    return conversar_em_partes(INSTRUCOES, montar_prompt(pergunta, artigos))
