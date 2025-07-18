from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from .message import Message
    from .dossier import Dossier


class ClientBase(BaseModel):
    telegram_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class Client(ClientBase):
    id: int
    created_at: datetime
    messages: List['Message'] = []
    dossier: Optional['Dossier'] = None

    class Config:
        from_attributes = True