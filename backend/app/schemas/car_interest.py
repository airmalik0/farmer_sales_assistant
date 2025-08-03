from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, ConfigDict


class CarInterestBase(BaseModel):
    client_id: int
    structured_data: Optional[Dict[str, Any]] = None


class CarInterestCreate(CarInterestBase):
    pass


class CarInterestUpdate(BaseModel):
    structured_data: Optional[Dict[str, Any]] = None


class CarQueryManualUpdate(BaseModel):
    """Schema for manual updates to a single car query"""
    brand: Optional[Union[str, List[str]]] = None
    model: Optional[Union[str, List[str]]] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    mileage_max: Optional[int] = None
    exterior_color: Optional[Union[str, List[str]]] = None
    interior_color: Optional[Union[str, List[str]]] = None
    engine_type: Optional[str] = None
    drive_type: Optional[str] = None
    notes: Optional[str] = None


class CarInterestManualUpdate(BaseModel):
    """Schema for manual updates to car interest queries by humans"""
    queries: Optional[List[CarQueryManualUpdate]] = None


class CarInterest(CarInterestBase):
    id: int
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True) 