from decouple import config
from telegram import Bot

secret_token = config('TOKEN', default='KEY')

TOKEN = config('TOKEN', default='KEY')
CHAT_ID = config('CHAT_ID', default='1')

bot = Bot(TOKEN)
