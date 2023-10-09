from asgiref.sync import sync_to_async
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from products.models import Product
from core.utils import get_ozon_product_url


async def get_latest_products(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Функция для вывода сообщением последних добавленных данных.

    Args:
        update: Класс, содержащий обновления из Telegram.
        context: контекст.
    """
    chat_id = update.effective_message.chat_id
    latest_products = list(Product.objects.filter(request_date = Product.objects.latest('request_date').request_date).values('name','ozon_id'))
    message = '\n'.join([f'{iterator+1}.{latest_products[iterator]["name"]}\n{get_ozon_product_url(latest_products[iterator]["ozon_id"])}' for iterator in range(len(latest_products))])
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
    )


async def wake_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = ReplyKeyboardMarkup([['Список товаров']])
    await context.bot.send_message(
        chat_id=chat.id,
        text='Спасибо, что вы включили меня, {}!'.format(name),
        reply_markup=button,
    )


def add_handlers(application: Application):
    """
    Adding handlers for events from Telegram
    """

    application.add_handler(CommandHandler('start', wake_up))
    application.add_handler(
        MessageHandler(filters.Regex('Список товаров'), get_latest_products)
    )
    return application
