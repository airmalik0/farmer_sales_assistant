from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    
    # Pact данные (основные идентификаторы)
    pact_conversation_id = Column(Integer, unique=True, nullable=False, index=True)
    pact_contact_id = Column(Integer, nullable=True)  # Может быть null пока не придет первое сообщение
    pact_company_id = Column(Integer, nullable=False)
    
    # Идентификаторы контакта
    sender_external_id = Column(String, nullable=False, index=True)  # phone/username от провайдера
    sender_external_public_id = Column(String, nullable=True)       # публичный ID
    
    # Информация о контакте
    name = Column(String, nullable=True)              # sender_name из Pact
    phone_number = Column(String, nullable=True)      # для WhatsApp
    username = Column(String, nullable=True)          # для Telegram Personal
    avatar_url = Column(String, nullable=True)
    
    # Канал и статус
    provider = Column(String, nullable=False)         # "whatsapp", "telegram_personal"
    operational_state = Column(String, default="open") # "open", "archived", "blocked" 
    replied_state = Column(String, default="initialized") # "initialized", "replied", "unreplied"
    
    # Системные поля
    name_approved = Column(Boolean, default=False)    # Для рассылок
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_pact_message_id = Column(Integer, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="client", order_by="Message.timestamp.desc()")
    dossier = relationship("Dossier", back_populates="client", uselist=False)
    car_interest = relationship("CarInterest", back_populates="client", uselist=False)
    tasks = relationship("Task", back_populates="client", order_by="Task.created_at.desc()")