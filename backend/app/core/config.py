import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./farmer_sales.db")
    
    # Telegram (только для админа)
    telegram_bot_token: str = ""
    farmer_telegram_id: int = 0
    
    # OpenAI
    openai_api_key: str = ""
    
    # LangSmith (опционально для трейсинга)
    langsmith_tracing: Optional[str] = os.getenv("LANGSMITH_TRACING")
    langsmith_api_key: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    langchain_tracing_v2: Optional[str] = os.getenv("LANGCHAIN_TRACING_V2", os.getenv("LANGSMITH_TRACING"))
    langchain_endpoint: Optional[str] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    langchain_api_key: Optional[str] = os.getenv("LANGCHAIN_API_KEY", os.getenv("LANGSMITH_API_KEY"))
    langchain_project: Optional[str] = os.getenv("LANGCHAIN_PROJECT", "farmer-crm-agents")
    
    # Google Sheets (опционально)
    google_sheets_spreadsheet_id: str = ""
    google_sheets_credentials_file: str = ""
    google_sheets_range: str = ""
    
    # Server
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    
    # Pact API V2
    pact_api_token: str = os.getenv("PACT_API_TOKEN", "")
    pact_company_id: int = int(os.getenv("PACT_COMPANY_ID", "0"))
    pact_api_url: str = os.getenv("PACT_API_URL", "https://api.pact.im")
    pact_webhook_secret: str = os.getenv("PACT_WEBHOOK_SECRET", "")  # Опционально - может отсутствовать
    pact_webhook_url: str = os.getenv("PACT_WEBHOOK_URL", "")  # Единый URL для всех webhook типов

    class Config:
        env_file = ".env"


settings = Settings()