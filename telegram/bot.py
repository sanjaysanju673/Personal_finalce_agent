from telegram import Update

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

from config.settings import (
    TELEGRAM_BOT_TOKEN
)

from workflows.stock_workflow import (
    run_workflow
)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Finance Agent Running 🚀"
    )

