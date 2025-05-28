# config.py
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")

ENDPOINTS_FUTUROS = {
    "World Cup":   "https://black-365.com/api/vet3/game?cate2=Soccer&title=World%20Cup&day=0",
    "Premiership": "https://black-365.com/api/vet3/game?cate2=Soccer&title=Premiership&day=0",
    "Euro Cup":    "https://black-365.com/api/vet3/game?cate2=Soccer&title=Euro%20Cup&day=0",
}
ENDPOINTS_PASSADOS = {
    "World Cup":   "https://black-365.com/api/vet3/game?cate2=Soccer&title=World%20Cup&day=1&flag=%EA%B2%BD%EA%B8%B0%EC%A2%85%EB%A3%8C",
    "Premiership": "https://black-365.com/api/vet3/game?cate2=Soccer&title=Premiership&day=1&flag=%EA%B2%BD%EA%B8%B0%EC%A2%85%EB%A3%8C",
    "Euro Cup":    "https://black-365.com/api/vet3/game?cate2=Soccer&title=Euro%20Cup&day=1&flag=%EA%B2%BD%EA%B8%B0%EC%A2%85%EB%A3%8C",
}
