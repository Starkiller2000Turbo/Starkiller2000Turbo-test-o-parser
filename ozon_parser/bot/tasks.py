from bot.utils import sync_send_message
from ozon_parser.celery import app, logger


@app.task
def send_message(message: str) -> None:
    """Функция для отправления сообщения в заданный чат.

    Args:
        message: сообщение, которое необходимо отправить.
    """
    logger.info('Отправляю сообщение в телеграм')
    sync_send_message(message)
    logger.info('Сообщение в телеграм отправлено')
