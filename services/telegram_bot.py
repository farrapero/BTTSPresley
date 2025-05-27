import logging
import requests


class TelegramBot:
    """
    Envia e edita mensagens no Telegram via HTTP.
    Formatação personalizada: liga com emoji, minuto, análise em bloco separado e link.
    """
    # Emojis por liga
    LEAGUE_EMOJIS = {
        "World Cup": "🌐",
        "Premiership": "🏆",
        "Euro Cup": "🇪🇺",
    }

    def __init__(self, token: str, chat_id: str):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        # Armazena os dados da mensagem para edição futura
        self._messages = {}

    def send_entry_message(self, league: str, home: str, away: str,
                           minute: int, justification: str, url: str) -> int:
        """
        Envia recomendação de entrada com o formato:

        <emoji> Liga — Time A x Time B
        ➡️ Minuto: MM'

        💡ANÁLISE: texto

        🔗Link: url

        Retorna o message_id para edições futuras.
        """
        emoji = self.LEAGUE_EMOJIS.get(league, "⚽")
        text = (
            f"{emoji} <b>{league}</b> — <i>{home} x {away}</i>\n"
            f"➡️ Minuto: {minute}'\n\n"
            f"💡<b>ANÁLISE:</b> {justification}\n\n"
            f"🔗Link: {url}"
        )
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            resp = requests.post(f"{self.base_url}/sendMessage", json=payload)
            resp.raise_for_status()
            msg_id = resp.json()["result"]["message_id"]
            # Armazena para editar depois
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
            self.logger.error(f"Erro ao enviar mensagem: {e}")
            return None

    def edit_result(self, message_id: int, success: bool) -> None:
        """
        Edita a mensagem anterior, inserindo ✅ ou ❌ após o minuto.
        Mantém o mesmo layout original.
        """
        data = self._messages.get(message_id)
        if not data:
            self.logger.error(f"Mensagem {message_id} não encontrada para edição")
            return

        result_emoji = "✅" if success else "❌"
        emoji = self.LEAGUE_EMOJIS.get(data["league"], "⚽")
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
            resp = requests.post(f"{self.base_url}/editMessageText", json=payload)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Erro ao editar mensagem: {e}")
