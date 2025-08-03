import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки бота"""
    
    def __init__(self):
        # Telegram
        self.bot_token: str = self._get_required_env("TELEGRAM_BOT_TOKEN")
        self.farmer_telegram_id: int = int(self._get_required_env("FARMER_TELEGRAM_ID"))
        
        # Backend API
        self.backend_url: str = self._get_required_env("BACKEND_URL")
        
        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    def _get_required_env(self, key: str) -> str:
        """Получает обязательную переменную окружения"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Переменная окружения {key} не установлена!")
        return value


# Глобальный экземпляр настроек
settings = Settings()

# Обратная совместимость
BOT_TOKEN = settings.bot_token
FARMER_TELEGRAM_ID = settings.farmer_telegram_id
BACKEND_URL = settings.backend_url
