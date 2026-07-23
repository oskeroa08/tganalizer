from telethon.sync import TelegramClient
from telethon.sessions.StringSession import StringSession

API_ID = 35674454  # Ваш API ID
API_HASH = "0ab360442bf470fa40c2a04fc0a36148" # Ваш API Hash

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("Ваша StringSession:")
    print(client.session.save())