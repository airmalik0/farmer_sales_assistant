from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


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
    notes: Optional[str] = None


class Dossier(DossierBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True