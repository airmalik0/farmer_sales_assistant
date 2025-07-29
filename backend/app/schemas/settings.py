from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SettingBase(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class SettingCreate(SettingBase):
    pass


class SettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Setting(SettingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GreetingRequest(BaseModel):
    greeting_text: str
    enabled: bool = True


class GreetingResponse(BaseModel):
    greeting_text: str
    enabled: bool
    is_custom: bool


class GreetingUpdateRequest(BaseModel):
    greeting_text: Optional[str] = None
    enabled: Optional[bool] = None 