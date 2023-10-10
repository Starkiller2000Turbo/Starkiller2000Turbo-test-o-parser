from asgiref.sync import async_to_sync
from decouple import config
from telegram import Bot

secret_token = config('TOKEN', default='KEY')

TOKEN = config('TOKEN', default='KEY')
CHAT_ID = config('CHAT_ID', default='1')

bot = Bot(TOKEN)


sync_send_message = async_to_sync(bot.send_message)
