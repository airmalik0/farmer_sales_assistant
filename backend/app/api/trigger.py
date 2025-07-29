from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas import trigger as trigger_schemas
from ..models.trigger import TriggerStatus
from ..services.trigger_service import TriggerService
from ..services.google_sheets_service import google_sheets_service
import asyncio

router = APIRouter()


@router.get("/", response_model=List[trigger_schemas.TriggerSummary])
def get_triggers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TriggerStatus] = None,
    db: Session = Depends(get_db)
):
    """Получить список триггеров"""
    triggers = TriggerService.get_triggers(db, skip=skip, limit=limit, status=status)
    return triggers


@router.get("/{trigger_id}", response_model=trigger_schemas.Trigger)
def get_trigger(trigger_id: int, db: Session = Depends(get_db)):
    """Получить триггер по ID"""
    trigger = TriggerService.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Триггер не найден")
    return trigger


@router.post("/", response_model=trigger_schemas.Trigger)
def create_trigger(
    trigger_data: trigger_schemas.TriggerCreate,
    db: Session = Depends(get_db)
):
    """Создать новый триггер"""
    try:
        trigger = TriggerService.create_trigger(db, trigger_data)
        return trigger
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{trigger_id}", response_model=trigger_schemas.Trigger)
def update_trigger(
    trigger_id: int,
    trigger_update: trigger_schemas.TriggerUpdate,
    db: Session = Depends(get_db)
):
    """Обновить триггер"""
    trigger = TriggerService.update_trigger(db, trigger_id, trigger_update)
    if not trigger:
        raise HTTPException(status_code=404, detail="Триггер не найден")
    return trigger


@router.delete("/{trigger_id}")
def delete_trigger(trigger_id: int, db: Session = Depends(get_db)):
    """Удалить триггер"""
    success = TriggerService.delete_trigger(db, trigger_id)
    if not success:
        raise HTTPException(status_code=404, detail="Триггер не найден")
    return {"message": "Триггер успешно удален"}


@router.post("/{trigger_id}/toggle")
def toggle_trigger_status(trigger_id: int, db: Session = Depends(get_db)):
    """Переключить статус триггера (активный/неактивный)"""
    trigger = TriggerService.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Триггер не найден")
    
    new_status = TriggerStatus.INACTIVE if trigger.status == TriggerStatus.ACTIVE else TriggerStatus.ACTIVE
    
    update_data = trigger_schemas.TriggerUpdate(status=new_status)
    updated_trigger = TriggerService.update_trigger(db, trigger_id, update_data)
    
    return {
        "message": f"Статус триггера изменен на {new_status.value}",
        "trigger": updated_trigger
    }


@router.post("/check-all")
async def check_all_triggers(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Проверить все активные триггеры вручную"""
    async def run_check():
        result = await TriggerService.check_all_triggers(db)
        return result
    
    background_tasks.add_task(run_check)
    return {"message": "Проверка триггеров запущена в фоновом режиме"}


@router.get("/check-all/sync")
async def check_all_triggers_sync(db: Session = Depends(get_db)):
    """Проверить все активные триггеры синхронно (для отладки)"""
    result = await TriggerService.check_all_triggers(db)
    return result


@router.post("/{trigger_id}/test")
async def test_trigger(
    trigger_id: int,
    car_id: Optional[str] = Query(None, description="ID автомобиля для тестирования"),
    db: Session = Depends(get_db)
):
    """Протестировать триггер на конкретном автомобиле или всех автомобилях"""
    trigger = TriggerService.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Триггер не найден")
    
    # Получаем данные из Google Sheets
    if car_id:
        car = google_sheets_service.get_car_by_id(car_id)
        if not car:
            raise HTTPException(status_code=404, detail=f"Автомобиль {car_id} не найден")
        cars = [car]
    else:
        cars = google_sheets_service.get_sheet_data()
        if not cars:
            raise HTTPException(status_code=503, detail="Нет данных из Google Sheets")
    
    # Тестируем триггер
    matched_cars = []
    for car in cars:
        if TriggerService.check_trigger_condition(trigger, car):
            matched_cars.append(car.to_dict())
    
    return {
        "trigger_name": trigger.name,
        "cars_tested": len(cars),
        "cars_matched": len(matched_cars),
        "matched_cars": matched_cars,
        "would_trigger": len(matched_cars) > 0
    }


@router.get("/{trigger_id}/logs", response_model=List[trigger_schemas.TriggerLog])
def get_trigger_logs(
    trigger_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить логи срабатывания конкретного триггера"""
    trigger = TriggerService.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Триггер не найден")
    
    logs = TriggerService.get_trigger_logs(db, trigger_id=trigger_id, skip=skip, limit=limit)
    return logs


@router.get("/{trigger_id}/stats")
def get_trigger_stats(trigger_id: int, db: Session = Depends(get_db)):
    """Получить статистику по триггеру"""
    trigger = TriggerService.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Триггер не найден")
    
    stats = TriggerService.get_trigger_stats(db, trigger_id)
    return stats


@router.get("/logs/all", response_model=List[trigger_schemas.TriggerLog])
def get_all_trigger_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить логи срабатывания всех триггеров"""
    logs = TriggerService.get_trigger_logs(db, skip=skip, limit=limit)
    return logs


# Google Sheets эндпоинты для отладки и управления
@router.get("/google-sheets/connection")
def check_google_sheets_connection():
    """Проверить подключение к Google Sheets"""
    is_connected = google_sheets_service.is_connected()
    return {
        "connected": is_connected,
        "spreadsheet_id": google_sheets_service.spreadsheet_id,
        "range": google_sheets_service.range_name
    }


@router.get("/google-sheets/headers")
def get_google_sheets_headers():
    """Получить заголовки столбцов из Google Sheets"""
    if not google_sheets_service.is_connected():
        raise HTTPException(status_code=503, detail="Нет подключения к Google Sheets")
    
    headers = google_sheets_service.get_headers()
    return {"headers": headers}


@router.get("/google-sheets/data")
def get_google_sheets_data(limit: int = Query(10, ge=1, le=100)):
    """Получить данные из Google Sheets (для отладки)"""
    if not google_sheets_service.is_connected():
        raise HTTPException(status_code=503, detail="Нет подключения к Google Sheets")
    
    cars = google_sheets_service.get_sheet_data()
    
    # Ограничиваем количество записей
    limited_cars = cars[:limit]
    
    return {
        "total_cars": len(cars),
        "returned_cars": len(limited_cars),
        "cars": [car.to_dict() for car in limited_cars]
    }


@router.get("/google-sheets/search")
def search_google_sheets_data(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    location: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    mileage_max: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """Поиск автомобилей в Google Sheets по критериям"""
    if not google_sheets_service.is_connected():
        raise HTTPException(status_code=503, detail="Нет подключения к Google Sheets")
    
    # Создаем словарь фильтров
    filters = {}
    if brand:
        filters['brand'] = brand
    if model:
        filters['model'] = model
    if location:
        filters['location'] = location
    if price_min is not None:
        filters['price_min'] = price_min
    if price_max is not None:
        filters['price_max'] = price_max
    if year_min is not None:
        filters['year_min'] = year_min
    if year_max is not None:
        filters['year_max'] = year_max
    if mileage_max is not None:
        filters['mileage_max'] = mileage_max
    if status:
        filters['status'] = status
    
    # Выполняем поиск
    cars = google_sheets_service.filter_cars(**filters)
    
    # Ограничиваем результаты
    limited_cars = cars[:limit]
    
    return {
        "filters_applied": filters,
        "total_matches": len(cars),
        "returned_results": len(limited_cars),
        "cars": [car.to_dict() for car in limited_cars]
    }


# Системные эндпоинты
@router.get("/system/status")
def get_system_status(db: Session = Depends(get_db)):
    """Получить общий статус системы триггеров"""
    # Подсчитываем триггеры по статусам
    active_triggers = len(TriggerService.get_triggers(db, status=TriggerStatus.ACTIVE, limit=1000))
    inactive_triggers = len(TriggerService.get_triggers(db, status=TriggerStatus.INACTIVE, limit=1000))
    paused_triggers = len(TriggerService.get_triggers(db, status=TriggerStatus.PAUSED, limit=1000))
    
    # Проверяем подключение к Google Sheets
    sheets_connected = google_sheets_service.is_connected()
    
    # Получаем последние логи
    recent_logs = TriggerService.get_trigger_logs(db, limit=10)
    
    return {
        "triggers": {
            "active": active_triggers,
            "inactive": inactive_triggers,
            "paused": paused_triggers,
            "total": active_triggers + inactive_triggers + paused_triggers
        },
        "google_sheets": {
            "connected": sheets_connected,
            "spreadsheet_id": google_sheets_service.spreadsheet_id if sheets_connected else None
        },
        "recent_activity": {
            "recent_triggers": len(recent_logs),
            "last_trigger_time": recent_logs[0].triggered_at if recent_logs else None
        }
    } 