from dotenv import load_dotenv
import os
load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "database/stock.db"
)