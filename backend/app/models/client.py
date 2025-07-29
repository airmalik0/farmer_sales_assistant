from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    name_approved = Column(Boolean, default=False, nullable=False)  # Одобрено ли имя для рассылки
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    messages = relationship("Message", back_populates="client", order_by="Message.timestamp.desc()")
    dossier = relationship("Dossier", back_populates="client", uselist=False)
    car_interest = relationship("CarInterest", back_populates="client", uselist=False)
    tasks = relationship("Task", back_populates="client", order_by="Task.created_at.desc()")