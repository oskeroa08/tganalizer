
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from config import load_config, save_config
import os

app = FastAPI(title="TG Analyzer Web Panel")

# Templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(TEMPLATES_DIR, exist_ok=True)


@app.get("/")
async def get_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
        return {"message": "Create index.html in templates folder"}
    return FileResponse(index_path)


@app.get("/api/config")
async def get_config():
    config = load_config()
    # Don't return sensitive data if needed, but for now return all
    return config


class ConfigUpdate(BaseModel):
    telegram: dict = None
    monitoring: dict = None
    subscribers: list = None
    admins: list = None
    filters: dict = None
    ai: dict = None
    web_panel: dict = None


@app.put("/api/config")
async def update_config(update: ConfigUpdate):
    config = load_config()
    if update.telegram:
        config["telegram"].update(update.telegram)
    if update.monitoring:
        config["monitoring"].update(update.monitoring)
    if update.subscribers is not None:
        config["subscribers"] = update.subscribers
    if update.admins is not None:
        config["admins"] = update.admins
    if update.filters:
        config["filters"].update(update.filters)
    if update.ai:
        config["ai"].update(update.ai)
    if update.web_panel:
        config["web_panel"].update(update.web_panel)
    save_config(config)
    return {"success": True, "config": config}


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

