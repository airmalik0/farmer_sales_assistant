from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from .message import Message
    from .dossier import Dossier
    from .car_interest import CarInterest
    from .task import Task


class ClientBase(BaseModel):
    # Pact данные
    pact_conversation_id: int
    pact_contact_id: Optional[int] = None
    pact_company_id: int
    
    # Идентификаторы контакта
    sender_external_id: str
    sender_external_public_id: Optional[str] = None
    
    # Информация о контакте
    name: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Канал и статус
    provider: str  # "whatsapp", "telegram_personal"
    operational_state: Optional[str] = "open"
    replied_state: Optional[str] = "initialized"
    
    # Системные поля
    name_approved: Optional[bool] = False


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    # Информация о контакте (только это можно обновлять через API)
    name: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Статусы
    operational_state: Optional[str] = None
    replied_state: Optional[str] = None
    name_approved: Optional[bool] = None


class Client(ClientBase):
    id: int
    name_approved: bool
    created_at: datetime
    last_message_at: Optional[datetime] = None
    last_pact_message_id: Optional[int] = None
    
    # Relationships
    messages: List['Message'] = []
    dossier: Optional['Dossier'] = None
    car_interest: Optional['CarInterest'] = None
    tasks: List['Task'] = []

    model_config = ConfigDict(from_attributes=True)


# Дополнительные схемы для админ API
class ClientStats(BaseModel):
    total: int
    whatsapp: int
    telegram_personal: int
    approved: int


class ClientSummary(BaseModel):
    id: int
    name: Optional[str]
    provider: str
    created_at: datetime
    last_message_at: Optional[datetime]
    messages_count: int