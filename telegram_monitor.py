
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import sys
import requests
import asyncio
from config import load_config, save_config
from filters import process_message
from ai_recognizer import analyze_message

def safe_print(text):
    """Print text safely, handling Unicode encoding errors on Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        encoded = text.encode(sys.stdout.encoding, errors='replace')
        print(encoded.decode(sys.stdout.encoding))


client = None
bot_client = None
bot_token = None
auth_state = {
    "step": "idle",  # idle, waiting_for_phone, waiting_for_code
    "phone": None,
    "phone_code_hash": None
}


def init_client(config):
    global client
    proxy = None
    
    if config["telegram"]["string_session"]:
        session = StringSession(config["telegram"]["string_session"])
    else:
        session = config["telegram"]["session_name"]
        
    client = TelegramClient(
        session,
        config["telegram"]["api_id"],
        config["telegram"]["api_hash"],
        proxy=proxy
    )
    return client


def init_bot(config):
    global bot_token, bot_client
    bot_token = config["telegram"]["bot_token"]
    bot_client = TelegramClient(
        "auth_bot_session",
        config["telegram"]["api_id"],
        config["telegram"]["api_hash"],
        proxy=None
    )
    return bot_client


async def send_via_bot(chat_id: int, text: str):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": text
        }
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.post(url, params=params, timeout=10)
        )
        response.raise_for_status()
        return True
    except Exception as e:
        safe_print(f"Error sending to bot chat {chat_id}: {e}")
        return False


async def notify_admins(text: str):
    config = load_config()
    for admin_id in config.get("admins", []):
        try:
            await send_via_bot(admin_id, text)
        except Exception as e:
            safe_print(f"Error notifying admin {admin_id}: {e}")


async def run_monitor():
    config = load_config()
    init_client(config)
    init_bot(config)
    
    # Setup auth bot handlers first
    @bot_client.on(events.NewMessage())
    async def auth_bot_handler(event):
        global auth_state
        config = load_config()
        
        # Only process messages from admins
        if event.chat_id not in config.get("admins", []):
            return
            
        message = event.message.text.strip()
        
        if message == "/startauth":
            auth_state["step"] = "waiting_for_phone"
            await event.reply("🔐 Начата авторизация! Отправьте номер телефона в формате /setphone +71234567890")
            return
            
        if auth_state["step"] == "waiting_for_phone":
            if message.startswith("/setphone "):
                phone = message.replace("/setphone ", "").strip()
                auth_state["phone"] = phone
                try:
                    await client.connect()
                    if not await client.is_user_authorized():
                        result = await client.send_code_request(phone)
                        auth_state["phone_code_hash"] = result.phone_code_hash
                        auth_state["step"] = "waiting_for_code"
                        await event.reply(f"✅ Код отправлен на {phone}! Отправьте код в формате /setcode 12345")
                    else:
                        auth_state["step"] = "idle"
                        await event.reply("✅ Клиент уже авторизован!")
                except Exception as e:
                    await event.reply(f"❌ Ошибка: {str(e)}")
                    auth_state["step"] = "idle"
            else:
                await event.reply("⚠️ Используйте /setphone +71234567890 для отправки номера телефона")
            return
            
        if auth_state["step"] == "waiting_for_code":
            if message.startswith("/setcode "):
                code = message.replace("/setcode ", "").strip()
                try:
                    await client.sign_in(
                        phone=auth_state["phone"],
                        code=code,
                        phone_code_hash=auth_state["phone_code_hash"]
                    )
                    session_string = client.session.save()
                    await event.reply(f"✅ Успешная авторизация!\n\nВаша StringSession (сохраните её в переменные окружения TELEGRAM_STRING_SESSION):\n```\n{session_string}\n```")
                    auth_state["step"] = "idle"
                except Exception as e:
                    await event.reply(f"❌ Ошибка авторизации: {str(e)}")
            else:
                await event.reply("⚠️ Используйте /setcode 12345 для отправки кода")
            return
            
        # If not in auth flow, send help
        await event.reply("📋 Доступные команды:\n/startauth — Начать авторизацию")
    
    # Start auth bot
    safe_print("Starting auth bot...")
    await bot_client.start(bot_token=bot_token)
    safe_print("Auth bot started!")
    
    # Try to start monitor client
    safe_print("Connecting to Telegram...")
    try:
        await client.start(phone=config["telegram"]["phone_number"])
        safe_print("Connected!")
    except Exception as e:
        safe_print(f"Monitor client not authorized yet: {e}")
        await notify_admins("⚠️ Клиент мониторинга не авторизован! Напишите /startauth боту для начала авторизации.")
        
    if client and await client.is_user_authorized():
        # Get all dialogs for reference
        dialogs = []
        async for dialog in client.iter_dialogs(limit=100):
            dialogs.append(dialog)

        target_chat_ids = config["monitoring"]["target_chat_ids"]
        if not target_chat_ids:
            safe_print("\nList of your chats (last 100):")
            for dialog in dialogs:
                chat_type = "?"
                if dialog.is_user:
                    chat_type = "PM"
                elif dialog.is_group:
                    chat_type = "Group"
                elif dialog.is_channel:
                    chat_type = "Channel"
                safe_print(f"  {chat_type} | ID: {dialog.id} | Name: {dialog.name}")
            safe_print("\nNo chats configured for monitoring! Use the web panel to add some.")

        safe_print(f"\nMonitoring chats: {[d.name for d in dialogs if d.id in target_chat_ids]}")
        safe_print("Waiting for new messages...")

        @client.on(events.NewMessage(chats=target_chat_ids))
        async def new_message_handler(event):
            try:
                msg = event.message
                sender = await msg.get_sender()
                sender_name = "Unknown"
                sender_id = "Unknown"
                sender_username = ""
                if sender:
                    sender_name = getattr(sender, 'first_name', "Unknown")
                    sender_id = getattr(sender, 'id', "Unknown")
                    username = getattr(sender, 'username', None)
                    if username:
                        sender_username = f"@{username}"
                
                # Get chat name
                chat_id = event.chat_id
                chat_name = "Unknown Chat"
                for dialog in dialogs:
                    if dialog.id == chat_id:
                        chat_name = dialog.name
                        break

                config = load_config()
                message_text = ""
                for attr in ['text', 'message', 'caption']:
                    val = getattr(msg, attr, None)
                    if val:
                        message_text = val.strip()
                        break
                
                filter_result = process_message(message_text, config)
                
                # AI analysis if enabled
                ai_result = None
                if config["ai"]["enabled"] and config["ai"]["groq_api_key"]:
                    ai_result = await analyze_message(message_text, config["ai"]["groq_api_key"])
                    if ai_result and ai_result.get("relevant"):
                        filter_result["should_send"] = True
                
                if not filter_result["should_send"]:
                    return

                # Format message
                priority_tag = "🚨 ВЫСОКИЙ ПРИОРИТЕТ " if filter_result["is_priority"] else ""
                ai_tag = "🤖 AI РЕЛЕВАНТНО " if (ai_result and ai_result.get("relevant")) else ""
                
                text = (
                    f"{priority_tag}{ai_tag}📩 НОВОЕ СООБЩЕНИЕ!\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📁 Чат: {chat_name}\n"
                    f"🆔 ID чата: {chat_id}\n"
                    f"👤 От: {sender_name}\n"
                    f"🆔 ID отправителя: {sender_id}\n"
                )
                if sender_username:
                    text += f"📌 Username: {sender_username}\n"
                
                if filter_result["priority_keyword"]:
                    text += f"⭐ Ключевое слово: {filter_result['priority_keyword']}\n"
                if ai_result and ai_result.get("reason"):
                    text += f"🤖 AI анализ: {ai_result['reason']}\n"
                    
                text += (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💬 Текст:\n{message_text}"
                )

                # Send to all admins via bot
                for admin_id in config.get("admins", []):
                    try:
                        await send_via_bot(admin_id, text)
                        safe_print("Пуш отправлен")
                    except Exception as e:
                        safe_print(f"Error sending to admin {admin_id}: {e}")
            except Exception as e:
                safe_print(f"Error in message handler: {e}")
                import traceback
                safe_print(traceback.format_exc())

    # Run both clients until disconnected
    await asyncio.gather(
        client.run_until_disconnected() if (client and await client.is_user_authorized()) else asyncio.sleep(0),
        bot_client.run_until_disconnected()
    )

