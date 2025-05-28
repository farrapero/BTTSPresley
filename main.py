import time
import logging

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from services.bet365 import fetch_future_matches, fetch_past_matches, calculate_btts_percentage
from services.gemini import GeminiClient
from services.telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    gemini = GeminiClient(history_limit=120)
    bot    = TelegramBot(token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID)
    active = None

    logger.info("Iniciando monitoramento...")
    while True:
        try:
            futures = fetch_future_matches()
            pasts   = fetch_past_matches(limit=120)
            pct     = calculate_btts_percentage(pasts)
            last20  = pasts[-20:]
            pct20   = calculate_btts_percentage(last20)

            if not active:
                sugg = gemini.choose_btts_match(futures, pasts, pct)
                sel_raw = sugg.get("selection")

                # tenta converter para inteiro
                try:
                    sel = int(sel_raw)
                except Exception:
                    # tenta mapear pelo formato "Home x Away"
                    sel = next(
                        (
                            i for i, m in enumerate(futures, start=1)
                            if f"{m['home']} x {m['away']}" == str(sel_raw)
                        ),
                        None
                    )

                # valida índice
                if not isinstance(sel, int) or not (1 <= sel <= len(futures)):
                    logger.error(f"Selection inválida: {sel_raw!r} | suggestion: {sugg}")
                    time.sleep(30)
                    continue

                match = futures[sel - 1]
                # extrai minuto de dateOrigin
                try:
                    minute = int(match["dateOrigin"].split()[1].split(":")[1])
                except Exception:
                    minute = 0

                justification = sugg.get("justification", "")
                url = f"https://www.bet365.bet.br/#/AVR/B146/R^{match['idx']}/"

                msg_id = bot.send_entry_message(
                    match["league"],
                    match["home"],
                    match["away"],
                    minute,
                    justification,
                    url,
                    pct20
                )
                if msg_id:
                    active = {"idx": match["idx"], "message_id": msg_id}
                    logger.info(
                        f"Enviada sugestão (idx={match['idx']}, minute={minute}, msg_id={msg_id})"
                    )

            else:
                done = next((m for m in pasts if m["idx"] == active["idx"]), None)
                if done:
                    bot.edit_result(active["message_id"], done["btts"])
                    logger.info(f"Editada msg {active['message_id']} — BTTS: {done['btts']}")
                    active = None

        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")

        time.sleep(30)

if __name__ == "__main__":
    main()
