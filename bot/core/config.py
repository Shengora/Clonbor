from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

DB_PATH = os.getenv("DB_PATH", "database.sqlite")
SOURCE_BOT_USERNAME = os.getenv("SOURCE_BOT_USERNAME", "@source_bot_here")
