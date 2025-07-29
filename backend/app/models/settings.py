from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from ..core.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GreetingSettings:
    """Константы для работы с настройками приветствия"""
    CUSTOM_GREETING_KEY = "custom_greeting"
    USE_CUSTOM_GREETING_KEY = "use_custom_greeting"
    
    @staticmethod
    def get_default_greeting():
        """Возвращает стандартное приветствие"""
        return "Добрый день, [Имя Клиента], как вы?" 