
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "35674454"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "0ab360442bf470fa40c2a04fc0a36148")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("="*60)
    print("Ваша StringSession (скопируйте это и добавьте в переменную окружения TELEGRAM_STRING_SESSION):")
    print("="*60)
    print(client.session.save())
    print("="*60)

