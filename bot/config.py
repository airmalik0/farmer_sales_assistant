import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FARMER_TELEGRAM_ID = int(os.getenv("FARMER_TELEGRAM_ID", "0"))

# Backend API
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://farmer:password@localhost:5432/farmer_crm")