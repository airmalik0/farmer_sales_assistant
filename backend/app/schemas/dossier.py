from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DossierBase(BaseModel):
    client_id: int
    summary: Optional[str] = None


class DossierCreate(DossierBase):
    pass


class DossierUpdate(BaseModel):
    summary: Optional[str] = None


class Dossier(DossierBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True