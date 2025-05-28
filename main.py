# main.py
import time
import logging

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from services.bet365 import fetch_future_matches, fetch_past_matches, calculate_btts_percentage
from services.gemini import GeminiClient
from services.telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    gemini = GeminiClient(history_limit=80)
    bot    = TelegramBot(token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID)
    active = None  # {'idx': ..., 'message_id': ...}

    logger.info("Iniciando o loop principal de monitoramento...")
    while True:
        try:
            # 1) carrega dados
            futures = fetch_future_matches()
            pasts   = fetch_past_matches(limit=80)
            pct     = calculate_btts_percentage(pasts)

            if not active:
                # 2) pede 1 sugestão
                suggestion = gemini.choose_btts_match(futures, pasts, pct)

                sel_raw = suggestion.get("selection")
                try:
                    sel = int(sel_raw)
                except (TypeError, ValueError):
                    logger.error(f"Selection inválida do Gemini: {sel_raw!r} | suggestion: {suggestion}")
                    time.sleep(30)
                    continue

                if not (1 <= sel <= len(futures)):
                    logger.error(f"Selection fora de intervalo: {sel} (1–{len(futures)})")
                    time.sleep(30)
                    continue

                match = futures[sel - 1]
                minute = int(match["dateOrigin"].split()[1].split(":")[1])
                justification = suggestion.get("justification", "")
                url = f"https://www.bet365.bet.br/#/AVR/B146/R^{match['idx']}/"

                msg_id = bot.send_entry_message(
                    match["league"], match["home"], match["away"],
                    minute, justification, url
                )
                if msg_id:
                    active = {"idx": match["idx"], "message_id": msg_id}
                    logger.info(
                        f"Enviada sugestão (idx={match['idx']}, msg_id={msg_id}, minute={minute})"
                    )

            else:
                # 3) aguarda resultado da partida ativa
                done = next((m for m in pasts if m["idx"] == active["idx"]), None)
                if done:
                    bot.edit_result(active["message_id"], done["btts"])
                    logger.info(f"Editada mensagem {active['message_id']} — BTTS: {done['btts']}")
                    active = None

        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")

        time.sleep(30)

if __name__ == "__main__":
    main()
