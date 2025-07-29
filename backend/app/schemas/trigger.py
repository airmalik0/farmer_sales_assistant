from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from ..models.trigger import TriggerStatus, TriggerAction


class TriggerConditions(BaseModel):
    """Схема для условий срабатывания триггера"""
    car_id: Optional[str] = Field(None, description="Конкретный ID автомобиля (например, GE-38)")
    brand: Optional[Union[str, List[str]]] = Field(None, description="Марка или список марок")
    model: Optional[Union[str, List[str]]] = Field(None, description="Модель или список моделей")
    location: Optional[str] = Field(None, description="Локация автомобиля")
    price_min: Optional[float] = Field(None, ge=0, description="Минимальная цена")
    price_max: Optional[float] = Field(None, ge=0, description="Максимальная цена")
    year_min: Optional[int] = Field(None, ge=1900, description="Минимальный год")
    year_max: Optional[int] = Field(None, ge=1900, description="Максимальный год")
    mileage_max: Optional[int] = Field(None, ge=0, description="Максимальный пробег")
    status: Optional[Union[str, List[str]]] = Field(None, description="Статус или список статусов")
    
    @validator('price_max')
    def price_max_greater_than_min(cls, v, values):
        if v is not None and 'price_min' in values and values['price_min'] is not None:
            if v <= values['price_min']:
                raise ValueError('price_max должна быть больше price_min')
        return v
    
    @validator('year_max')
    def year_max_greater_than_min(cls, v, values):
        if v is not None and 'year_min' in values and values['year_min'] is not None:
            if v < values['year_min']:
                raise ValueError('year_max должен быть больше или равен year_min')
        return v


class TriggerActionConfig(BaseModel):
    """Базовая схема для конфигурации действий триггера"""
    pass


class NotifyActionConfig(TriggerActionConfig):
    """Конфигурация для действия уведомления"""
    message: str = Field(..., description="Текст уведомления")
    channels: List[str] = Field(default=["websocket"], description="Каналы для отправки")
    
    @validator('channels')
    def validate_channels(cls, v):
        allowed_channels = ["websocket", "telegram", "email"]
        for channel in v:
            if channel not in allowed_channels:
                raise ValueError(f"Неподдерживаемый канал: {channel}")
        return v


class CreateTaskActionConfig(TriggerActionConfig):
    """Конфигурация для создания задачи"""
    title: str = Field(..., description="Заголовок задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    priority: Optional[str] = Field("medium", description="Приоритет задачи")
    
    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ["low", "medium", "high", "urgent"]
        if v not in allowed_priorities:
            raise ValueError(f"Неподдерживаемый приоритет: {v}")
        return v


class WebhookActionConfig(TriggerActionConfig):
    """Конфигурация для webhook"""
    url: str = Field(..., description="URL для webhook")
    method: str = Field(default="POST", description="HTTP метод")
    headers: Optional[Dict[str, str]] = Field(default={}, description="HTTP заголовки")
    
    @validator('method')
    def validate_method(cls, v):
        allowed_methods = ["GET", "POST", "PUT", "PATCH"]
        if v.upper() not in allowed_methods:
            raise ValueError(f"Неподдерживаемый HTTP метод: {v}")
        return v.upper()


class TriggerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название триггера")
    description: Optional[str] = Field(None, description="Описание триггера")
    status: TriggerStatus = Field(default=TriggerStatus.ACTIVE, description="Статус триггера")
    conditions: TriggerConditions = Field(..., description="Условия срабатывания")
    action_type: TriggerAction = Field(..., description="Тип действия")
    action_config: Optional[Dict[str, Any]] = Field(None, description="Конфигурация действия")
    check_interval_minutes: int = Field(default=5, ge=1, le=1440, description="Интервал проверки в минутах")


class TriggerCreate(TriggerBase):
    pass


class TriggerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TriggerStatus] = None
    conditions: Optional[TriggerConditions] = None
    action_type: Optional[TriggerAction] = None
    action_config: Optional[Dict[str, Any]] = None
    check_interval_minutes: Optional[int] = Field(None, ge=1, le=1440)


class TriggerLogBase(BaseModel):
    trigger_id: int
    trigger_data: Optional[Dict[str, Any]] = None
    action_result: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


class TriggerLogCreate(TriggerLogBase):
    pass


class TriggerLog(TriggerLogBase):
    id: int
    triggered_at: datetime
    
    class Config:
        from_attributes = True


class Trigger(TriggerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_checked_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    trigger_count: int
    trigger_logs: Optional[List[TriggerLog]] = None
    
    class Config:
        from_attributes = True


class TriggerSummary(BaseModel):
    """Краткая информация о триггере для списков"""
    id: int
    name: str
    status: TriggerStatus
    action_type: TriggerAction
    trigger_count: int
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 