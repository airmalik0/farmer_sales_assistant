from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
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
    sender = Column(Enum(SenderType), nullable=False)
    content_type = Column(String, nullable=False)  # text, voice, video_note, document, photo
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    client = relationship("Client", back_populates="messages")