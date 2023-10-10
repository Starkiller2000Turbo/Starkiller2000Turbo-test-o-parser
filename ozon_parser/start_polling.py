import os

import django
from telegram import Update
from telegram.ext import Application

from bot.bot import CHAT_ID, TOKEN, sync_send_message
from bot.handlers import add_handlers
from core.utils import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ozon_parser.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()


def start_pulling() -> None:
    """Запуск Telegram-бота."""
    logging.info('Started script')
    application = Application.builder().token(TOKEN).build()
    logging.info('created application')
    application = add_handlers(application)
    logging.info('Added handlers')
    sync_send_message(CHAT_ID, '👋')
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logging.info('Application running')


if __name__ == '__main__':
    start_pulling()
