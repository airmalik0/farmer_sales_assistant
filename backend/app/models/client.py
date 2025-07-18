from sqlalchemy import Column, Integer, String, DateTime, BigInteger
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    messages = relationship("Message", back_populates="client")
    dossier = relationship("Dossier", back_populates="client", uselist=False)