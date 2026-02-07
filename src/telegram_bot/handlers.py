"""Telegram command and button handlers."""
import logging
from typing import Callable

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters

from src.telegram_bot.monitoring import (
    get_monitoring_chats,
    save_monitoring_chats,
    ensure_monitoring_job,
    stop_monitoring_job,
    create_broadcast_callback,
    MONITORING_INTERVAL,
)

logger = logging.getLogger(__name__)

BTN_SEARCH = "🔍 Search"
BTN_MONITORING_ON = "▶️ Monitoring On"
BTN_MONITORING_OFF = "⏹ Monitoring Off"


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_SEARCH)],
            [KeyboardButton(BTN_MONITORING_ON), KeyboardButton(BTN_MONITORING_OFF)],
        ],
        resize_keyboard=True,
    )


def register_handlers(
    application: Application,
    *,
    get_tasks_text: Callable[[], str],
    get_tasks_list: Callable[[], list],
) -> None:
    """Register all handlers. get_tasks_text for /search; get_tasks_list for monitoring."""
    broadcast_callback = create_broadcast_callback(get_tasks_list)

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        menu = (
            "Welcome!\n\n"
            "**Menu:**\n\n"
            "/search — Run check and get current task list.\n\n"
            "/monitoring on — Notify you when the task list changes.\n\n"
            "/monitoring off — Stop monitoring.\n\n"
            "You can use the buttons below or type the commands."
        )
        await update.message.reply_text(
            menu, reply_markup=get_main_keyboard(), parse_mode="Markdown"
        )

    async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = get_tasks_text()
        await update.message.reply_text(f"Search result:\n{result}")

    async def monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args or len(context.args) != 1:
            await update.message.reply_text("Usage: /monitoring on  or  /monitoring off")
            return
        arg = context.args[0].lower()
        if arg not in ("on", "off"):
            await update.message.reply_text("Usage: /monitoring on  or  /monitoring off")
            return
        chats = get_monitoring_chats(context)
        if arg == "on":
            chats.add(update.effective_chat.id)
            save_monitoring_chats(application)
            if not ensure_monitoring_job(application, broadcast_callback):
                await update.message.reply_text(
                    "Monitoring could not start: job queue is not available. "
                    "Install with: pip install 'python-telegram-bot[job-queue]'"
                )
                return
            await update.message.reply_text(
                f"Monitoring is ON. You will be notified when the task list changes (check every {MONITORING_INTERVAL}s)."
            )
        else:
            chats.discard(update.effective_chat.id)
            save_monitoring_chats(application)
            if not chats:
                stop_monitoring_job(application)
            await update.message.reply_text("Monitoring is OFF.")

    async def button_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = get_tasks_text()
        await update.message.reply_text(f"Search result:\n{result}")

    async def button_monitoring_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chats = get_monitoring_chats(context)
        chats.add(update.effective_chat.id)
        save_monitoring_chats(application)
        if not ensure_monitoring_job(application, broadcast_callback):
            await update.message.reply_text(
                "Monitoring could not start: job queue is not available. "
                "Install with: pip install 'python-telegram-bot[job-queue]'"
            )
            return
        await update.message.reply_text(
            f"Monitoring is ON. You will be notified when the task list changes (check every {MONITORING_INTERVAL}s)."
        )

    async def button_monitoring_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chats = get_monitoring_chats(context)
        chats.discard(update.effective_chat.id)
        save_monitoring_chats(application)
        if not chats:
            stop_monitoring_job(application)
        await update.message.reply_text("Monitoring is OFF.")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("monitoring", monitoring))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_SEARCH}$"), button_search))
    application.add_handler(
        MessageHandler(filters.Regex(f"^{BTN_MONITORING_ON}$"), button_monitoring_on)
    )
    application.add_handler(
        MessageHandler(filters.Regex(f"^{BTN_MONITORING_OFF}$"), button_monitoring_off)
    )
