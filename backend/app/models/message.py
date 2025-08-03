from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class SenderType(enum.Enum):
    client = "client"
    farmer = "farmer"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Pact данные
    pact_message_id = Column(Integer, unique=True, nullable=True)  # ID в Pact
    external_id = Column(String, nullable=True)                   # ID от провайдера
    external_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Сообщение
    sender = Column(Enum(SenderType), nullable=False)  # client, farmer
    content_type = Column(String, nullable=False)      # text, attachment
    content = Column(Text, nullable=True)               # текст сообщения
    
    # Статус и метаданные
    income = Column(Boolean, nullable=False)            # входящее/исходящее
    status = Column(String, default="created")          # created, sent, delivered, read, error
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ответы и реакции
    replied_to_id = Column(String, nullable=True)      # external_id сообщения на которое отвечаем
    reactions = Column(JSON, default=list)
    details = Column(JSON, nullable=True)              # данные об ошибках доставки
    
    # Relationships
    client = relationship("Client", back_populates="messages")
    attachments = relationship("MessageAttachment", back_populates="message")


class MessageAttachment(Base):
    __tablename__ = "message_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # Pact данные
    pact_attachment_id = Column(Integer, nullable=True)
    
    # Файл
    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    attachment_url = Column(String, nullable=False)
    preview_url = Column(String, nullable=True)
    
    # Метаданные
    aspect_ratio = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    push_to_talk = Column(Boolean, default=False)  # для голосовых
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message", back_populates="attachments")