from datetime import datetime, date
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    client_id: int
    description: str
    due_date: Optional[datetime] = None
    is_completed: bool = False
    priority: str = "normal"  # normal, high, low
    source: str = "manual"  # manual, trigger, ai
    trigger_id: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    priority: Optional[str] = None
    telegram_notification_sent: Optional[bool] = None


class TaskManualUpdate(BaseModel):
    """Schema for manual updates to task fields by humans"""
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    priority: Optional[str] = None  # normal, high, low


class TaskWithTrigger(BaseModel):
    """Schema для создания задачи с триггером"""
    client_id: int
    description: str
    due_date: Optional[datetime] = None
    priority: str = "normal"
    
    # Настройки триггера
    trigger_name: str
    trigger_conditions: Dict[str, Any]
    trigger_action_config: Optional[Dict[str, Any]] = None


class Task(TaskBase):
    id: int
    telegram_notification_sent: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 