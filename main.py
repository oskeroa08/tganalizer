
import asyncio
import threading
import uvicorn
from web_panel import app
from telegram_monitor import run_monitor
from config import load_config


def run_web_panel(config):
    uvicorn.run(
        app,
        host=config["web_panel"]["host"],
        port=config["web_panel"]["port"],
        log_level="info"
    )


async def main():
    config = load_config()
    
    # Run web panel in a separate thread
    web_thread = threading.Thread(target=run_web_panel, args=(config,), daemon=True)
    web_thread.start()
    
    print(f"Web panel started at http://{config['web_panel']['host']}:{config['web_panel']['port']}")
    
    # Run Telegram monitor
    await run_monitor()


if __name__ == "__main__":
    asyncio.run(main())

