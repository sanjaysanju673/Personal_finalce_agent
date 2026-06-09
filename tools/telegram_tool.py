import requests

from config.settings import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID
)
from config.logging_config import get_logger

logger = get_logger(__name__)

def send(message):
    logger.debug(f"Preparing to send Telegram message")

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}"
        f"/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        logger.info(
            "Telegram message sent successfully."
        )

    except Exception as e:

        logger.error(
            f"Telegram Error: {e}", exc_info=True
        )


def send_file(file_path, caption=None):
    """Send a file (document) to Telegram chat as an attachment."""
    logger.debug(f"Preparing to send file {file_path} to Telegram")

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}"
        f"/sendDocument"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID , 
    }

    if caption:
        data["caption"] = caption

    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            response = requests.post(
                url,
                data=data,
                files=files,
                timeout=60
            )
            response.raise_for_status()

        logger.info(f"Telegram file sent successfully: {file_path}")

    except Exception as e:
        logger.error(f"Telegram file send error: {e}", exc_info=True)