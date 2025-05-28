import time
import logging

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from services.bet365 import fetch_future_matches, fetch_past_matches, calculate_btts_percentage
from services.gemini import GeminiClient
from services.telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    # Inicia cliente Gemini e bot Telegram
    gemini = GeminiClient(history_limit=80)
    bot    = TelegramBot(token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID)
    active = None  # mantém partida ativa e message_id

    logger.info("Iniciando o loop principal de monitoramento...")
    while True:
        try:
            # 1) Coleta dados das APIs
            futures = fetch_future_matches()
            pasts   = fetch_past_matches(limit=80)
            pct     = calculate_btts_percentage(pasts)

            if not active:
                # 2) Solicita sugestão ao Gemini
                suggestion = gemini.choose_btts_match(futures, pasts, pct)

                # Captura seleção bruta
                sel_raw = suggestion.get("selection")
                sel = None
                # Tenta converter em inteiro
                try:
                    sel = int(sel_raw)
                except Exception:
                    # Se for texto no formato "Home x Away", mapeia para índice
                    if isinstance(sel_raw, str) and ' x ' in sel_raw:
                        home_sel, away_sel = [s.strip() for s in sel_raw.split(' x ', 1)]
                        for i, m in enumerate(futures, start=1):
                            if m['home'] == home_sel and m['away'] == away_sel:
                                sel = i
                                break
                # Valida índice
                if not sel or not (1 <= sel <= len(futures)):
                    logger.error(f"Selection inválida do Gemini: {sel_raw!r} | suggestion: {suggestion}")
                    time.sleep(30)
                    continue

                # Monta dados da partida escolhida
                match = futures[sel - 1]
                try:
                    minute = int(match["dateOrigin"].split()[1].split(":")[1])
                except Exception:
                    minute = 0
                justification = suggestion.get("justification", "")
                url = f"https://www.bet365.bet.br/#/AVR/B146/R^{match['idx']}/"

                # 3) Envia mensagem no Telegram
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
                # 4) Verifica resultado da partida ativa
                done = next((m for m in pasts if m["idx"] == active["idx"]), None)
                if done:
                    bot.edit_result(active["message_id"], done["btts"])
                    logger.info(
                        f"Editada mensagem {active['message_id']} — BTTS: {done['btts']}"
                    )
                    active = None

        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")

        # 5) Aguarda antes de próxima iteração
        time.sleep(30)

if __name__ == "__main__":
    main()
