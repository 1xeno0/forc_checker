"""Monitoring state and job: persist chat IDs, run periodic check, notify on change."""
import json
import logging
from pathlib import Path
from typing import Callable

from telegram.ext import Application, ContextTypes

logger = logging.getLogger(__name__)

# Paths: pathlib and / work the same on Linux and Windows
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = _PROJECT_ROOT / "monitoring_chats.json"

MONITORING_JOB_NAME = "monitoring_broadcast"
MONITORING_INTERVAL = 60


def load_monitoring_chats() -> set:
    if not STATE_FILE.exists():
        return set()
    try:
        data = STATE_FILE.read_text(encoding="utf-8")
        return set(json.loads(data))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load monitoring state: %s", e)
        return set()


def save_monitoring_chats(application: Application) -> None:
    chats = application.bot_data.get("monitoring_chats") or set()
    try:
        STATE_FILE.write_text(json.dumps(sorted(chats), indent=0), encoding="utf-8")
    except OSError as e:
        logger.warning("Could not save monitoring state: %s", e)


def get_monitoring_chats(context: ContextTypes.DEFAULT_TYPE) -> set:
    if "monitoring_chats" not in context.application.bot_data:
        context.application.bot_data["monitoring_chats"] = set()
    return context.application.bot_data["monitoring_chats"]


def create_broadcast_callback(get_tasks_list: Callable[[], list]):
    """Return an async callback for the job queue that notifies only on task list change."""

    async def broadcast(context: ContextTypes.DEFAULT_TYPE) -> None:
        monitoring_chats = context.application.bot_data.get("monitoring_chats") or set()
        if not monitoring_chats:
            return
        try:
            current_tasks = get_tasks_list()
        except Exception as e:
            logger.exception("Checker failed in monitoring")
            err_msg = f"⚠️ Monitoring check failed: {e!s}"
            for chat_id in list(monitoring_chats):
                try:
                    await context.bot.send_message(chat_id=chat_id, text=err_msg)
                except Exception as send_err:
                    logger.warning("Could not send error to %s: %s", chat_id, send_err)
                    monitoring_chats.discard(chat_id)
                    save_monitoring_chats(context.application)
            return
        last_tasks = context.application.bot_data.get("last_monitoring_tasks")
        if current_tasks == last_tasks:
            return
        context.application.bot_data["last_monitoring_tasks"] = current_tasks
        text = "Task list changed:\n" + (
            "\n".join(current_tasks) if current_tasks else "No tasks."
        )
        for chat_id in list(monitoring_chats):
            try:
                await context.bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                logger.warning("Could not send to %s: %s", chat_id, e)
                monitoring_chats.discard(chat_id)
                save_monitoring_chats(context.application)

    return broadcast


def ensure_monitoring_job(application: Application, callback) -> bool:
    """Schedule the monitoring job. Returns False if job queue is not available."""
    if application.job_queue is None:
        logger.warning(
            "Job queue is not available. Install with: pip install 'python-telegram-bot[job-queue]'"
        )
        return False
    if not application.job_queue.get_jobs_by_name(MONITORING_JOB_NAME):
        application.job_queue.run_repeating(
            callback,
            interval=MONITORING_INTERVAL,
            first=0,
            name=MONITORING_JOB_NAME,
        )
    return True


def stop_monitoring_job(application: Application) -> None:
    if application.job_queue is None:
        return
    for job in application.job_queue.get_jobs_by_name(MONITORING_JOB_NAME):
        job.schedule_removal()
