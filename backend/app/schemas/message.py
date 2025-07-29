from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class SenderType(str, Enum):
    client = "client"
    farmer = "farmer"


class MessageBase(BaseModel):
    client_id: int
    sender: SenderType
    content_type: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content_type: Optional[str] = None
    content: Optional[str] = None


class Message(MessageBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True