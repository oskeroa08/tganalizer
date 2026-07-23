
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DEFAULT_CONFIG = {
    "telegram": {
        "api_id": int(os.getenv("TELEGRAM_API_ID", "35674454")),
        "api_hash": os.getenv("TELEGRAM_API_HASH", "0ab360442bf470fa40c2a04fc0a36148"),
        "phone_number": os.getenv("TELEGRAM_PHONE_NUMBER", "+967780166840"),
        "session_name": os.getenv("TELEGRAM_SESSION_NAME", "tg_monitor_session_new"),
        "string_session": os.getenv("TELEGRAM_STRING_SESSION", ""),
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", "")
    },
    "monitoring": {
        "target_chat_ids": []
    },
    "admins": [],
    "filters": {
        "keywords": [],
        "priority_keywords": ["срочно"]
    },
    "ai": {
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        "enabled": os.getenv("AI_ENABLED", "false").lower() == "true"
    },
    "web_panel": {
        "host": os.getenv("WEB_HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))
    }
}

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "data", "config.json")
DATA_DIR = os.path.dirname(CONFIG_PATH)


def load_config():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Merge with defaults, but override sensitive fields from environment variables
        merged = {**DEFAULT_CONFIG, **config}
        
        # Always use env vars for sensitive fields
        merged["telegram"]["api_id"] = int(os.getenv("TELEGRAM_API_ID", str(DEFAULT_CONFIG["telegram"]["api_id"])))
        merged["telegram"]["api_hash"] = os.getenv("TELEGRAM_API_HASH", DEFAULT_CONFIG["telegram"]["api_hash"])
        merged["telegram"]["phone_number"] = os.getenv("TELEGRAM_PHONE_NUMBER", DEFAULT_CONFIG["telegram"]["phone_number"])
        merged["telegram"]["session_name"] = os.getenv("TELEGRAM_SESSION_NAME", DEFAULT_CONFIG["telegram"]["session_name"])
        merged["telegram"]["string_session"] = os.getenv("TELEGRAM_STRING_SESSION", DEFAULT_CONFIG["telegram"]["string_session"])
        merged["telegram"]["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN", DEFAULT_CONFIG["telegram"]["bot_token"])
        merged["ai"]["groq_api_key"] = os.getenv("GROQ_API_KEY", DEFAULT_CONFIG["ai"]["groq_api_key"])
        merged["ai"]["enabled"] = os.getenv("AI_ENABLED", "true" if DEFAULT_CONFIG["ai"]["enabled"] else "false").lower() == "true"
        merged["web_panel"]["host"] = os.getenv("WEB_HOST", DEFAULT_CONFIG["web_panel"]["host"])
        merged["web_panel"]["port"] = int(os.getenv("PORT", os.getenv("WEB_PORT", str(DEFAULT_CONFIG["web_panel"]["port"]))))
        
        for key in DEFAULT_CONFIG:
            if isinstance(DEFAULT_CONFIG[key], dict) and isinstance(config.get(key), dict):
                # For non-sensitive nested fields, merge as before
                if key not in ["telegram", "ai", "web_panel"]:
                    merged[key] = {**DEFAULT_CONFIG[key], **config[key]}
        
        return merged
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return DEFAULT_CONFIG


def save_config(config):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    # Don't save sensitive data to config.json, keep them in env vars only
    config_to_save = {**config}
    # Don't save sensitive fields to file
    config_to_save["telegram"]["api_id"] = DEFAULT_CONFIG["telegram"]["api_id"]
    config_to_save["telegram"]["api_hash"] = ""
    config_to_save["telegram"]["phone_number"] = ""
    config_to_save["telegram"]["bot_token"] = ""
    config_to_save["ai"]["groq_api_key"] = ""
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_to_save, f, ensure_ascii=False, indent=2)

