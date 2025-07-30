import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FARMER_TELEGRAM_ID = int(os.getenv("FARMER_TELEGRAM_ID"))

# Backend API
BACKEND_URL = os.getenv("BACKEND_URL")
