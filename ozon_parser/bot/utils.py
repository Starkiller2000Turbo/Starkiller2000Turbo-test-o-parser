from asyncio import get_event_loop, ensure_future, new_event_loop, set_event_loop
from telegram.error import TelegramError

from bot.bot import CHAT_ID, bot
from ozon_parser.celery import logger


def sync_send_message(message: str) -> None:
    """Функция для синхронного отправления сообщения.

    Args:
        message: сообщение, которое требуется передать.
    """
    try:
        loop = new_event_loop()
        set_event_loop(loop)
        loop.run_until_complete(bot.send_message(CHAT_ID, message))
    except TelegramError as e:
        logger.error(f'Error sending message to Telegram: {e}')
