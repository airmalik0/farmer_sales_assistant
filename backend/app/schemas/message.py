from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from enum import Enum


class SenderType(str, Enum):
    client = "client"
    farmer = "farmer"


class MessageAttachmentBase(BaseModel):
    file_name: str
    mime_type: str
    size: int
    attachment_url: str
    preview_url: Optional[str] = None
    aspect_ratio: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    push_to_talk: Optional[bool] = False


class MessageAttachmentCreate(MessageAttachmentBase):
    pact_attachment_id: Optional[int] = None


class MessageAttachment(MessageAttachmentBase):
    id: int
    message_id: int
    pact_attachment_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageBase(BaseModel):
    client_id: int
    sender: SenderType
    content_type: str  # "text", "attachment"
    content: Optional[str] = None  # Текст сообщения (может отсутствовать для attachment)
    income: bool  # True для входящих, False для исходящих
    status: Optional[str] = "created"
    replied_to_id: Optional[str] = None
    reactions: Optional[List[Any]] = []
    details: Optional[dict] = None


class MessageCreate(MessageBase):
    # Pact данные (опциональные при создании через API)
    pact_message_id: Optional[int] = None
    external_id: Optional[str] = None
    external_created_at: Optional[datetime] = None


class MessageUpdate(BaseModel):
    content_type: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    reactions: Optional[List[Any]] = None
    details: Optional[dict] = None


class Message(MessageBase):
    id: int
    pact_message_id: Optional[int] = None
    external_id: Optional[str] = None
    external_created_at: Optional[datetime] = None
    timestamp: datetime
    
    # Relationships
    attachments: List[MessageAttachment] = []

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat() if value else None

    @field_serializer('external_created_at')
    def serialize_external_created_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None

    model_config = ConfigDict(from_attributes=True)


# Дополнительные схемы для API
class MessageStats(BaseModel):
    total: int
    incoming: int
    outgoing: int


class MessageWithClient(Message):
    client_name: Optional[str] = None
    client_provider: str


# Схема для отправки сообщений через Pact
class PactMessageSend(BaseModel):
    text: Optional[str] = None
    attachment_ids: Optional[List[int]] = None
    replied_to_id: Optional[str] = None