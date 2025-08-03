from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class DossierBase(BaseModel):
    client_id: int
    structured_data: Optional[Dict[str, Any]] = None


class DossierCreate(DossierBase):
    pass


class DossierUpdate(BaseModel):
    structured_data: Optional[Dict[str, Any]] = None


class DossierManualUpdate(BaseModel):
    """Schema for manual updates to dossier fields by humans"""
    phone: Optional[str] = None
    current_location: Optional[str] = None
    birthday: Optional[str] = None  # Format: YYYY-MM-DD
    gender: Optional[str] = None  # "male" or "female"
    client_type: Optional[str] = None  # "private", "reseller", "broker", "dealer", "transporter"
    personal_notes: Optional[str] = None  # Личные заметки о клиенте
    business_profile: Optional[str] = None  # Бизнес-профиль (только для бизнес-клиентов)


class Dossier(DossierBase):
    id: int
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)