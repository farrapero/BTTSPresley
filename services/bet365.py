import requests
from config import ENDPOINTS_FUTUROS, ENDPOINTS_PASSADOS
from utils.translators import translate_team


def fetch_matches(url: str) -> list:
    """
    Faz GET na URL e retorna lista de objetos JSON.
    """
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def fetch_future_matches() -> list:
    """
    Busca próximas partidas de todas as ligas, desduplica, traduz nomes e
    extrai a odd de BTTS (ratio3, se presente).
    Retorna lista de dicts com:
      - idx, league, dateOrigin, home, away, ratio_btts (float ou None)
    """
    out = []
    for league, url in ENDPOINTS_FUTUROS.items():
        data = fetch_matches(url)
        seen = set()
        for item in data:
            idx = item.get("idx")
            if idx in seen:
                continue
            seen.add(idx)

            home = translate_team(item.get("home", ""))
            away = translate_team(item.get("away", ""))
            try:
                ratio_btts = float(item.get("ratio3"))
            except (TypeError, ValueError):
                ratio_btts = None

            out.append({
                "idx": idx,
                "league": league,
                "dateOrigin": item.get("dateOrigin"),
                "home": home,
                "away": away,
                "ratio_btts": ratio_btts
            })
    # Ordena por dateOrigin
    out.sort(key=lambda x: x["dateOrigin"])
    return out


def fetch_past_matches(limit: int = 50) -> list:
    """
    Busca resultados passados (limit máximo por liga), retorna lista de dicts:
      - idx, league, home, away, home_goals, away_goals, btts (bool)
    """
    out = []
    for league, url in ENDPOINTS_PASSADOS.items():
        data = fetch_matches(url)
        for item in data[:limit]:
            try:
                home_goals = int(item.get("result1"))
                away_goals = int(item.get("result2"))
            except (TypeError, ValueError):
                continue

            home = translate_team(item.get("home", ""))
            away = translate_team(item.get("away", ""))
            out.append({
                "idx": item.get("idx"),
                "league": league,
                "home": home,
                "away": away,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "btts": home_goals > 0 and away_goals > 0
            })
    return out


def calculate_btts_percentage(past_matches: list) -> float:
    """
    % de BTTS no histórico
    """
    if not past_matches:
        return 0.0
    total = len(past_matches)
    count = sum(1 for m in past_matches if m.get("btts"))
    return (count / total) * 100.0
