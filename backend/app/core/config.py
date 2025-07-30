import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Telegram
    telegram_bot_token: str
    farmer_telegram_id: int
    
    # OpenAI
    openai_api_key: str
    
    # Google Sheets
    google_sheets_credentials_file: Optional[str] = None
    google_sheets_spreadsheet_id: Optional[str] = None
    google_sheets_range: Optional[str] = None
    
    # Server
    backend_url: str = "http://localhost:8000"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = Settings()