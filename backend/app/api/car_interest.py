from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
from ..core.database import get_db
from ..schemas import car_interest as car_interest_schemas
from ..services.car_interest_service import CarInterestService
from ..services.client_service import ClientService
from .websocket import notify_car_interest_update
import asyncio

router = APIRouter()


@router.get("/client/{client_id}", response_model=car_interest_schemas.CarInterest)
def get_car_interest_by_client(client_id: int, db: Session = Depends(get_db)):
    """Получить автомобильные интересы клиента"""
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    car_interest = CarInterestService.get_car_interest_by_client(db, client_id=client_id)
    if car_interest is None:
        raise HTTPException(status_code=404, detail="Автомобильные интересы не найдены")
    return car_interest


@router.get("/{car_interest_id}", response_model=car_interest_schemas.CarInterest)
def get_car_interest(car_interest_id: int, db: Session = Depends(get_db)):
    """Получить автомобильные интересы по ID"""
    car_interest = CarInterestService.get_car_interest(db, car_interest_id=car_interest_id)
    if car_interest is None:
        raise HTTPException(status_code=404, detail="Автомобильные интересы не найдены")
    return car_interest


@router.post("/", response_model=car_interest_schemas.CarInterest)
async def create_car_interest(car_interest: car_interest_schemas.CarInterestCreate, db: Session = Depends(get_db)):
    """Создать новые автомобильные интересы"""
    # Проверяем, что клиент существует
    client = ClientService.get_client(db, car_interest.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Проверяем, что автомобильные интересы еще не существуют
    existing_car_interest = CarInterestService.get_car_interest_by_client(db, car_interest.client_id)
    if existing_car_interest:
        raise HTTPException(status_code=400, detail="Автомобильные интересы для этого клиента уже существуют")
    
    created_car_interest = CarInterestService.create_car_interest(db=db, car_interest=car_interest)
    
    # Уведомляем фронтенд о создании автомобильных интересов
    await notify_car_interest_update(
        client_id=created_car_interest.client_id,
        car_interest_data={
            "id": created_car_interest.id,
            "client_id": created_car_interest.client_id,
            "structured_data": created_car_interest.structured_data,
            "last_updated": created_car_interest.last_updated.isoformat() if created_car_interest.last_updated else None
        }
    )
    
    return created_car_interest


@router.put("/{car_interest_id}", response_model=car_interest_schemas.CarInterest)
async def update_car_interest(
    car_interest_id: int, 
    car_interest_update: car_interest_schemas.CarInterestUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить автомобильные интересы"""
    car_interest = CarInterestService.update_car_interest(db, car_interest_id=car_interest_id, car_interest_update=car_interest_update)
    if car_interest is None:
        raise HTTPException(status_code=404, detail="Автомобильные интересы не найдены")
    
    # Уведомляем фронтенд об обновлении автомобильных интересов
    await notify_car_interest_update(
        client_id=car_interest.client_id,
        car_interest_data={
            "id": car_interest.id,
            "client_id": car_interest.client_id,
            "structured_data": car_interest.structured_data,
            "last_updated": car_interest.last_updated.isoformat() if car_interest.last_updated else None
        }
    )
    
    return car_interest


@router.put("/client/{client_id}", response_model=car_interest_schemas.CarInterest)
async def update_or_create_car_interest_by_client(
    client_id: int,
    structured_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Обновить или создать автомобильные интересы для клиента"""
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Получаем или создаем автомобильные интересы
    car_interest = CarInterestService.get_car_interest_by_client(db, client_id)
    if car_interest:
        # Обновляем существующие автомобильные интересы
        car_interest_update = car_interest_schemas.CarInterestUpdate(structured_data=structured_data)
        updated_car_interest = CarInterestService.update_car_interest(db, car_interest.id, car_interest_update)
    else:
        # Создаем новые автомобильные интересы
        car_interest_create = car_interest_schemas.CarInterestCreate(client_id=client_id, structured_data=structured_data)
        updated_car_interest = CarInterestService.create_car_interest(db, car_interest_create)
    
    if updated_car_interest:
        # Уведомляем фронтенд
        await notify_car_interest_update(
            client_id=updated_car_interest.client_id,
            car_interest_data={
                "id": updated_car_interest.id,
                "client_id": updated_car_interest.client_id,
                "structured_data": updated_car_interest.structured_data,
                "last_updated": updated_car_interest.last_updated.isoformat() if updated_car_interest.last_updated else None
            }
        )
    
    return updated_car_interest


@router.put("/{car_interest_id}/manual", response_model=car_interest_schemas.CarInterest)
async def update_car_interest_manually(
    car_interest_id: int,
    manual_update: car_interest_schemas.CarInterestManualUpdate,
    db: Session = Depends(get_db)
):
    """Ручное обновление автомобильных интересов с отметкой о ручном изменении"""
    
    # Получаем существующие автомобильные интересы
    car_interest = CarInterestService.get_car_interest(db, car_interest_id)
    if not car_interest:
        raise HTTPException(status_code=404, detail="Автомобильные интересы не найдены")
    
    # Получаем текущие данные
    current_data = car_interest.structured_data or {}
    existing_queries = current_data.get("queries", [])
    manual_modifications = current_data.get("manual_modifications", {})
    
    # Обновляем запросы если переданы
    update_data = manual_update.model_dump(exclude_unset=True)
    current_time = datetime.utcnow().isoformat()
    
    new_queries = []
    
    if "queries" in update_data and update_data["queries"] is not None:
        new_queries_data = update_data["queries"]
        
        for i, new_query in enumerate(new_queries_data):
            # Если это обновление существующего запроса
            if i < len(existing_queries):
                existing_query = existing_queries[i]
                updated_query = existing_query.copy()
                
                # Обрабатываем new_query как dict, а не как объект Pydantic
                if hasattr(new_query, 'model_dump'):
                    new_query_data = new_query.model_dump(exclude_unset=True)
                else:
                    new_query_data = new_query
                
                # Сравниваем и обновляем только измененные поля
                for field, new_value in new_query_data.items():
                    existing_value = existing_query.get(field)
                    
                    # Нормализуем значения для сравнения
                    normalized_existing = existing_value if existing_value is not None else ""
                    normalized_new = new_value if new_value is not None else ""
                    
                    # Если значение действительно изменилось
                    if normalized_existing != normalized_new:
                        updated_query[field] = new_value
                        # Отмечаем поле как измененное вручную
                        field_key = f"queries.{i}.{field}"
                        manual_modifications[field_key] = {
                            "modified_at": current_time,
                            "modified_by": "human"
                        }
                
                new_queries.append(updated_query)
            else:
                # Это новый запрос - добавляем все его поля как измененные вручную
                if hasattr(new_query, 'model_dump'):
                    new_query_data = new_query.model_dump(exclude_unset=True)
                else:
                    new_query_data = new_query
                    
                new_queries.append(new_query_data)
                
                # Отмечаем все поля нового запроса как измененные вручную
                for field in new_query_data.keys():
                    if new_query_data[field] is not None and new_query_data[field] != "":
                        field_key = f"queries.{i}.{field}"
                        manual_modifications[field_key] = {
                            "modified_at": current_time,
                            "modified_by": "human"
                        }
        
        # Если новых запросов меньше, чем было - добавляем оставшиеся старые
        if len(new_queries) < len(existing_queries):
            for i in range(len(new_queries), len(existing_queries)):
                new_queries.append(existing_queries[i])
    else:
        # Если queries не переданы, оставляем существующие
        new_queries = existing_queries
    
    # Формируем обновленную структуру данных
    new_structured_data = {
        **current_data,
        "queries": new_queries,
        "manual_modifications": manual_modifications
    }
    
    # Обновляем автомобильные интересы
    car_interest_update = car_interest_schemas.CarInterestUpdate(structured_data=new_structured_data)
    updated_car_interest = CarInterestService.update_car_interest(db, car_interest_id, car_interest_update)
    
    if updated_car_interest:
        # Уведомляем фронтенд об обновлении
        await notify_car_interest_update(
            client_id=updated_car_interest.client_id,
            car_interest_data={
                "id": updated_car_interest.id,
                "client_id": updated_car_interest.client_id,
                "structured_data": updated_car_interest.structured_data,
                "last_updated": updated_car_interest.last_updated.isoformat() if updated_car_interest.last_updated else None
            }
        )
    
    return updated_car_interest


@router.put("/client/{client_id}/manual", response_model=car_interest_schemas.CarInterest)
async def update_car_interest_manually_by_client(
    client_id: int,
    manual_update: car_interest_schemas.CarInterestManualUpdate,
    db: Session = Depends(get_db)
):
    """Ручное обновление автомобильных интересов клиента с отметкой о ручном изменении"""
    
    # Проверяем, что клиент существует
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Получаем или создаем автомобильные интересы
    car_interest = CarInterestService.get_car_interest_by_client(db, client_id)
    if not car_interest:
        # Создаем новые автомобильные интересы если их нет
        car_interest_create = car_interest_schemas.CarInterestCreate(
            client_id=client_id,
            structured_data={"queries": [], "manual_modifications": {}}
        )
        car_interest = CarInterestService.create_car_interest(db, car_interest_create)
    
    # Используем endpoint обновления по ID
    return await update_car_interest_manually(car_interest.id, manual_update, db) 