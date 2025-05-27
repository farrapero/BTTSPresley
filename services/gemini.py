import os
import json
import requests

class GeminiClient:
    """
    Cliente para a API Generative Language (Gemini free) via REST.
    Foca apenas no histórico: sequências e tendências, sem considerar odds.
    """
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Chave GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
        self.url = (
            f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
            f"?key={self.api_key}"
        )

    def choose_btts_match(self, future_matches: list, past_matches: list, btts_pct: float) -> dict:
        """
        Usa somente dados históricos para escolher partida com maior chance de BTTS.

        Retorna JSON com:
          selection (int): posição na lista de futuras (1-based)
          estimated_probability (float %)
          justification (str)
        """
        # Construir histórico: últimas 50 e sequência dos 10 mais recentes
        hist_50 = past_matches[-50:]
        last10 = hist_50[-10:]
        seq10 = ''.join('1' if m['btts'] else '0' for m in last10)

        prompt = (
            f"Você é um analista de dados de futebol virtual.\n"
            f"Histórico das últimas 50 partidas: {len(hist_50)} jogos, com {btts_pct:.1f}% BTTS.\n"
            f"Sequência dos últimos 10 jogos (1=BTTS,0=sem BTTS): {seq10}\n"
            "Não considere odds de mercado, pois não representam BTTS aqui.\n"
            "Abaixo, listadas as próximas partidas virtuais (numeradas):\n"
        )
        for i, m in enumerate(future_matches, start=1):
            prompt += f"{i}. [{m['league']}] {m['home']} x {m['away']} (origem: {m['dateOrigin']})\n"
        prompt += (
            "\nCom base exclusivamente no histórico e padrões recentes, "
            "analise tendências e escolha UMA partida com maior probabilidade de BTTS. "
            "Retorne um JSON com 'selection', 'estimated_probability' e 'justification'."
        )

        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.15, "candidateCount": 1, "maxOutputTokens": 512}
        }
        resp = requests.post(self.url, json=body)
        resp.raise_for_status()
        data = resp.json()

        cands = data.get("candidates", [])
        if not cands:
            raise ValueError(f"Nenhum candidato retornado: {data}")
        text = cands[0]["content"]["parts"][0]["text"].strip()
        if text.startswith("```"):
            lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"JSON inválido: {text}")
