import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./farmer_sales.db"
    
    # Telegram (только для админа)
    telegram_bot_token: str = ""
    farmer_telegram_id: int = 0
    
    # OpenAI
    openai_api_key: str = ""
    
    # Google Sheets (опционально)
    google_sheets_spreadsheet_id: str = ""
    google_sheets_credentials_file: str = ""
    google_sheets_range: str = ""
    
    # Server
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    
    # Pact API V2
    pact_api_token: str = ""
    pact_company_id: int = 0  # Опционально - можно получить из webhook'ов
    pact_api_url: str = "https://api.pact.im"
    pact_webhook_secret: str = ""  # Опционально - может отсутствовать
    pact_webhook_url: str = ""  # Единый URL для всех webhook типов

    class Config:
        env_file = ".env"


settings = Settings()