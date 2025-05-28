import os
import json
import requests

class GeminiClient:
    """
    Cliente Gemini free via REST, usando até 120 resultados históricos.
    """
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash", history_limit: int = 120):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")
        self.url = (
            f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
            f"?key={self.api_key}"
        )
        self.history_limit = history_limit

    def choose_btts_match(self, future_matches: list, past_matches: list, btts_pct: float) -> dict:
        """
        Gera prompt com:
         - Até history_limit partidas (agora 120).
         - Streaks de 3,4,5.
         - Janelas de 5,10,20.
         - Correlação com Over/Under e placares exatos.
        Retorna JSON com:
         - selection (int 1-based)
         - estimated_probability (float %)
         - justification (str)
        """
        history = past_matches[-self.history_limit:]
        seq3  = ''.join('1' if m['btts'] else '0' for m in history[-3:])
        seq4  = ''.join('1' if m['btts'] else '0' for m in history[-4:])
        seq5  = ''.join('1' if m['btts'] else '0' for m in history[-5:])
        wnd5  = history[-5:]
        wnd10 = history[-10:]
        wnd20 = history[-20:]

        prompt = (
            "Você é um analista de dados de futebol virtual.\n"
            f"Últimas {len(history)} partidas: {btts_pct:.1f}% BTTS.\n"
            f"Streaks: 3→{seq3}, 4→{seq4}, 5→{seq5}.\n"
            f"Janelas (5/10/20): {len(wnd5)}/{len(wnd10)}/{len(wnd20)} jogos.\n"
            "Considere Over/Under 1.5 e 2.5 e placares exatos comuns.\n"
            "Próximas partidas (lista numerada):\n"
        )
        for i, m in enumerate(future_matches, start=1):
            prompt += f"{i}. [{m['league']}] {m['home']} x {m['away']} (origem: {m['dateOrigin']})\n"
        prompt += (
            "\nCom base nestes dados, escolha UMA partida com maior probabilidade de BTTS. "
            "Retorne um JSON com: 'selection', 'estimated_probability', 'justification'. Sem texto adicional."
        )

        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "candidateCount": 1, "maxOutputTokens": 1024}
        }
        resp = requests.post(self.url, json=body)
        resp.raise_for_status()
        data = resp.json()

        cand = data.get("candidates", [])
        if not cand:
            raise ValueError(f"Nenhum candidato: {data}")
        raw = cand[0]["content"]["parts"][0]["text"].strip()
        if raw.startswith("```"):
            raw = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("```"))
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"Resposta inválida: {raw}")
