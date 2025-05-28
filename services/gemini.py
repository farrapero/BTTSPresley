import os
import json
import requests

class GeminiClient:
    """
    Cliente para a API Generative Language (Gemini free) via REST.
    Usa análises históricas aprofundadas (até 80 jogos).
    """
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash", history_limit: int = 80):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Chave GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
        self.url = (
            f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
            f"?key={self.api_key}"
        )
        self.history_limit = history_limit

    def choose_btts_match(self, future_matches: list, past_matches: list, btts_pct: float) -> dict:
        """
        Escolhe partida com base em análise de:
          - Up to history_limit partidas (agora 80) para frequências e streaks
          - Streaks de 3,4,5 resultados
          - Janelas de 5,10,20 partidas
          - Correlação com Over/Under e placares exatos
        Retorna JSON com:
          - selection (int, 1-based)
          - estimated_probability (float %)
          - justification (str)
        """
        # Recorta o histórico para as últimas history_limit partidas
        history = past_matches[-self.history_limit:]
        # Sequências finais de 3/4/5
        seq3 = ''.join('1' if m['btts'] else '0' for m in history[-3:])
        seq4 = ''.join('1' if m['btts'] else '0' for m in history[-4:])
        seq5 = ''.join('1' if m['btts'] else '0' for m in history[-5:])
        # Janelas deslizantes de 5,10,20
        wnd5  = history[-5:]
        wnd10 = history[-10:]
        wnd20 = history[-20:]

        prompt = (
            "Você é um analista de dados de futebol virtual.\n"
            f"Histórico últimas {len(history)} partidas: {btts_pct:.1f}% BTTS.\n"
            f"Streaks recentes: 3→{seq3}, 4→{seq4}, 5→{seq5}.\n"
            f"Janelas (5/10/20): {len(wnd5)}/{len(wnd10)}/{len(wnd20)} partidas.\n"
            "Considere correlação com mercados Over/Under 1.5 e 2.5 e placares exatos comuns.\n"
            "Próximas partidas virtuais (lista numerada):\n"
        )
        for i, m in enumerate(future_matches, start=1):
            prompt += f"{i}. [{m['league']}] {m['home']} x {m['away']} (origem: {m['dateOrigin']})\n"
        prompt += (
            "\nCom base exclusivamente nestes dados, escolha UMA partida com maior probabilidade de BTTS. "
            "Retorne um JSON com: 'selection', 'estimated_probability' e 'justification'. Sem texto adicional."
        )

        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "candidateCount": 1, "maxOutputTokens": 1024}
        }
        resp = requests.post(self.url, json=body)
        resp.raise_for_status()
        data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError(f"Nenhum candidato retornado: {data}")
        raw = candidates[0]["content"]["parts"][0]["text"].strip()

        # Limpeza de blocos Markdown
        if raw.startswith("```"):
            lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("```")]
            raw = "\n".join(lines)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"JSON inválido do Gemini: {raw}")
