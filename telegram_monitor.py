
from telethon import TelegramClient, events
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
        # Encode with errors replaced and print bytes as string
        encoded = text.encode(sys.stdout.encoding, errors='replace')
        print(encoded.decode(sys.stdout.encoding))


client = None
bot_token = None


def init_client(config):
    global client
    proxy = None
    client = TelegramClient(
        config["telegram"]["session_name"],
        config["telegram"]["api_id"],
        config["telegram"]["api_hash"],
        proxy=proxy
    )
    return client


def init_bot(config):
    global bot_token
    bot_token = config["telegram"]["bot_token"]
    return bot_token


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


async def run_monitor():
    config = load_config()
    init_client(config)
    init_bot(config)
    
    safe_print("Connecting to Telegram...")
    await client.start(phone=config["telegram"]["phone_number"])
    safe_print("Connected!")

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

    await client.run_until_disconnected()

