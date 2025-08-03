from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)  # Дата и время выполнения задачи
    is_completed = Column(Boolean, default=False, nullable=False)  # Статус выполнения
    priority = Column(String(20), default="normal", nullable=False)  # normal, high, low
    
    # Поддержка триггеров
    source = Column(String(50), default="manual", nullable=False)  # manual, trigger, ai
    trigger_id = Column(Integer, ForeignKey("triggers.id"), nullable=True)  # Ссылка на триггер
    extra_data = Column(JSON, nullable=True)  # Дополнительные данные (для триггеров)
    
    # Уведомления
    telegram_notification_sent = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="tasks")
    trigger = relationship("Trigger", foreign_keys=[trigger_id]) 