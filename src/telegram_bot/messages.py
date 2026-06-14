"""Telegram message sending helpers."""
from typing import Any

from telegram import Bot, Message

TELEGRAM_SAFE_MESSAGE_LIMIT = 3900


def split_telegram_message(
    text: str, limit: int = TELEGRAM_SAFE_MESSAGE_LIMIT
) -> list[str]:
    """Split text into Telegram-safe chunks, preserving line breaks when possible."""
    if limit <= 0:
        raise ValueError("Message limit must be positive")

    if not text:
        return []

    chunks: list[str] = []
    remaining_text = text

    while len(remaining_text) > limit:
        split_at = remaining_text.rfind("\n", 0, limit + 1)
        if split_at <= 0:
            split_at = limit
            chunk = remaining_text[:split_at]
        else:
            split_at += 1
            chunk = remaining_text[:split_at].rstrip("\n")

        if chunk:
            chunks.append(chunk)
        remaining_text = remaining_text[split_at:]

    if remaining_text:
        chunks.append(remaining_text)

    return chunks


async def reply_long_text(message: Message, text: str, **kwargs: Any) -> None:
    """Reply with text, splitting it into multiple Telegram messages if needed."""
    for chunk in split_telegram_message(text):
        await message.reply_text(chunk, **kwargs)


async def send_long_text(bot: Bot, chat_id: int, text: str, **kwargs: Any) -> None:
    """Send text to a chat, splitting it into multiple Telegram messages if needed."""
    for chunk in split_telegram_message(text):
        await bot.send_message(chat_id=chat_id, text=chunk, **kwargs)
