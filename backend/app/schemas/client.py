from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from .message import Message
    from .dossier import Dossier
    from .car_interest import CarInterest
    from .task import Task


class ClientBase(BaseModel):
    telegram_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    name_approved: Optional[bool] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    name_approved: Optional[bool] = None


class Client(ClientBase):
    id: int
    name_approved: bool
    created_at: datetime
    messages: List['Message'] = []
    dossier: Optional['Dossier'] = None
    car_interest: Optional['CarInterest'] = None
    tasks: List['Task'] = []

    class Config:
        from_attributes = True