import logging
import requests

class TelegramBot:
    """
    Envia e edita mensagens no Telegram via HTTP.
    Inclui linha de aviso das últimas 20 partidas.
    """
    LEAGUE_EMOJIS = {
        "World Cup":   "🌐",
        "Premiership": "🏆",
        "Euro Cup":    "🇪🇺",
    }

    def __init__(self, token: str, chat_id: str):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self._messages = {}

    def send_entry_message(self,
                           league: str,
                           home: str,
                           away: str,
                           minute: int,
                           justification: str,
                           url: str,
                           last20_pct: float) -> int:
        """
        Formato:
        <emoji> Liga — Time A x Time B
        ➡️ Minuto: MM'

        💡ANÁLISE: texto

        ⚠️ Últimas 20 partidas: X% BTTS.

        🔗Link: url
        """
        emoji = self.LEAGUE_EMOJIS.get(league, "⚽")
        text = (
            f"{emoji} <b>{league}</b> — <i>{home} x {away}</i>\n"
            f"➡️ Minuto: {minute}'\n\n"
            f"💡<b>ANÁLISE:</b> {justification}\n\n"
            f"⚠️ Últimas 20 partidas: {last20_pct:.1f}% BTTS.\n\n"
            f"🔗Link: {url}"
        )
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
        try:
            r = requests.post(f"{self.base_url}/sendMessage", json=payload)
            r.raise_for_status()
            msg_id = r.json()["result"]["message_id"]
            self._messages[msg_id] = {
                "league": league,
                "home": home,
                "away": away,
                "minute": minute,
                "justification": justification,
                "url": url
            }
            return msg_id
        except requests.RequestException as e:
            self.logger.error(f"Erro ao enviar: {e}")
            return None

    def edit_result(self, message_id: int, success: bool) -> None:
        data = self._messages.get(message_id)
        if not data:
            self.logger.error(f"Msg {message_id} não encontrada")
            return
        emoji = self.LEAGUE_EMOJIS.get(data["league"], "⚽")
        result_emoji = "✅" if success else "❌"
        text = (
            f"{emoji} <b>{data['league']}</b> — <i>{data['home']} x {data['away']}</i>\n"
            f"➡️ Minuto: {data['minute']}' {result_emoji}\n\n"
            f"💡<b>ANÁLISE:</b> {data['justification']}\n\n"
            f"🔗Link: {data['url']}"
        )
        payload = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            r = requests.post(f"{self.base_url}/editMessageText", json=payload)
            r.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Erro ao editar: {e}")
