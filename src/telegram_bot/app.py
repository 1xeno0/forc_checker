"""Build and run the Telegram bot."""
import logging

from telegram.ext import Application

from config import BOT_TOKEN, URL
from src.checker import CheckerClient
from src.telegram_bot.handlers import register_handlers
from src.telegram_bot.monitoring import (
    load_monitoring_chats,
    ensure_monitoring_job,
    create_broadcast_callback,
)
from telegram import Update

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

_checker = CheckerClient(url=URL)


def _get_tasks_text() -> str:
    try:
        tasks = _checker.session()
        return "\n".join(tasks) if tasks else "No tasks."
    except Exception as e:
        logger.exception("Checker failed")
        return f"Error: {e}"


def _get_tasks_list() -> list:
    return _checker.session()


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.bot_data["monitoring_chats"] = load_monitoring_chats()
    if application.bot_data["monitoring_chats"]:
        ensure_monitoring_job(application, create_broadcast_callback(_get_tasks_list))

    register_handlers(
        application,
        get_tasks_text=_get_tasks_text,
        get_tasks_list=_get_tasks_list,
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)
