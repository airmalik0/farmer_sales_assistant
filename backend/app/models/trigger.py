from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum


class TriggerStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"


class TriggerAction(enum.Enum):
    NOTIFY = "notify"
    CREATE_TASK = "create_task"
    SEND_MESSAGE = "send_message"
    WEBHOOK = "webhook"


class Trigger(Base):
    __tablename__ = "triggers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Статус триггера
    status = Column(SQLEnum(TriggerStatus), default=TriggerStatus.ACTIVE, nullable=False)
    
    # Условия срабатывания (JSON структура)
    conditions = Column(JSON, nullable=False)
    # Примеры структуры conditions:
    # {
    #   "car_id": "GE-38",  # конкретный автомобиль
    #   "brand": ["BMW", "AUDI"],  # список марок
    #   "location": "Авто в Тбилиси",  # конкретная локация
    #   "price_max": 50000,  # максимальная цена
    #   "price_min": 20000,  # минимальная цена
    #   "status": ["в продаже"]  # статусы
    # }
    
    # Действия при срабатывании
    action_type = Column(SQLEnum(TriggerAction), nullable=False)
    action_config = Column(JSON, nullable=True)
    # Примеры action_config:
    # Для NOTIFY: {"message": "BMW дешевле $50k найден!", "channels": ["telegram", "websocket"]}
    # Для CREATE_TASK: {"title": "Проверить BMW", "description": "Новый BMW дешевле 50k"}
    # Для WEBHOOK: {"url": "https://example.com/webhook", "method": "POST"}
    
    # Настройки частоты проверки
    check_interval_minutes = Column(Integer, default=5, nullable=False)  # как часто проверять
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Статистика
    trigger_count = Column(Integer, default=0, nullable=False)  # сколько раз сработал
    
    # Relationships
    trigger_logs = relationship("TriggerLog", back_populates="trigger", cascade="all, delete-orphan")


class TriggerLog(Base):
    __tablename__ = "trigger_logs"

    id = Column(Integer, primary_key=True, index=True)
    trigger_id = Column(Integer, ForeignKey("triggers.id"), nullable=False, index=True)
    
    # Данные о срабатывании
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    trigger_data = Column(JSON, nullable=True)  # данные, которые вызвали срабатывание
    action_result = Column(JSON, nullable=True)  # результат выполнения действия
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    trigger = relationship("Trigger", back_populates="trigger_logs") 