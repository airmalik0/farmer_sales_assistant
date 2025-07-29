import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://farmer:password@localhost:5432/farmer_crm")
    
    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    farmer_telegram_id: int = int(os.getenv("FARMER_TELEGRAM_ID", "0"))
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Google Sheets
    google_sheets_credentials_file: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
    google_sheets_spreadsheet_id: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    google_sheets_range: str = os.getenv("GOOGLE_SHEETS_RANGE", "Sheet1!A:Z")
    
    # Server
    host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    class Config:
        env_file = ".env"


settings = Settings()