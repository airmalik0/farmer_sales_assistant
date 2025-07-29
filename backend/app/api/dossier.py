from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
from ..core.database import get_db
from ..schemas import dossier as dossier_schemas
from ..services.dossier_service import DossierService
from ..services.client_service import ClientService
from .websocket import notify_dossier_update
import asyncio

router = APIRouter()


@router.get("/client/{client_id}", response_model=dossier_schemas.Dossier)
def get_dossier_by_client(client_id: int, db: Session = Depends(get_db)):
    """Получить досье клиента"""
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    dossier = DossierService.get_dossier_by_client(db, client_id=client_id)
    if dossier is None:
        raise HTTPException(status_code=404, detail="Досье не найдено")
    return dossier


@router.get("/{dossier_id}", response_model=dossier_schemas.Dossier)
def get_dossier(dossier_id: int, db: Session = Depends(get_db)):
    """Получить досье по ID"""
    dossier = DossierService.get_dossier(db, dossier_id=dossier_id)
    if dossier is None:
        raise HTTPException(status_code=404, detail="Досье не найдено")
    return dossier


@router.post("/", response_model=dossier_schemas.Dossier)
async def create_dossier(dossier: dossier_schemas.DossierCreate, db: Session = Depends(get_db)):
    """Создать новое досье"""
    # Проверяем, что клиент существует
    client = ClientService.get_client(db, dossier.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Проверяем, что досье еще не существует
    existing_dossier = DossierService.get_dossier_by_client(db, dossier.client_id)
    if existing_dossier:
        raise HTTPException(status_code=400, detail="Досье для этого клиента уже существует")
    
    created_dossier = DossierService.create_dossier(db=db, dossier=dossier)
    
    # Уведомляем фронтенд о создании досье
    await notify_dossier_update(
        client_id=created_dossier.client_id,
        dossier_data={
            "id": created_dossier.id,
            "client_id": created_dossier.client_id,
            "structured_data": created_dossier.structured_data,
            "last_updated": created_dossier.last_updated.isoformat() if created_dossier.last_updated else None
        }
    )
    
    return created_dossier


@router.put("/{dossier_id}", response_model=dossier_schemas.Dossier)
async def update_dossier(
    dossier_id: int, 
    dossier_update: dossier_schemas.DossierUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить досье"""
    dossier = DossierService.update_dossier(db, dossier_id=dossier_id, dossier_update=dossier_update)
    if dossier is None:
        raise HTTPException(status_code=404, detail="Досье не найдено")
    
    # Уведомляем фронтенд об обновлении досье
    await notify_dossier_update(
        client_id=dossier.client_id,
        dossier_data={
            "id": dossier.id,
            "client_id": dossier.client_id,
            "structured_data": dossier.structured_data,
            "last_updated": dossier.last_updated.isoformat() if dossier.last_updated else None
        }
    )
    
    return dossier


@router.put("/client/{client_id}", response_model=dossier_schemas.Dossier)
async def update_or_create_dossier_by_client(
    client_id: int,
    structured_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Обновить или создать досье для клиента"""
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Получаем или создаем досье
    dossier = DossierService.get_dossier_by_client(db, client_id)
    if dossier:
        # Обновляем существующее досье
        dossier_update = dossier_schemas.DossierUpdate(structured_data=structured_data)
        updated_dossier = DossierService.update_dossier(db, dossier.id, dossier_update)
    else:
        # Создаем новое досье
        dossier_create = dossier_schemas.DossierCreate(client_id=client_id, structured_data=structured_data)
        updated_dossier = DossierService.create_dossier(db, dossier_create)
    
    if updated_dossier:
        # Уведомляем фронтенд
        await notify_dossier_update(
            client_id=updated_dossier.client_id,
            dossier_data={
                "id": updated_dossier.id,
                "client_id": updated_dossier.client_id,
                "structured_data": updated_dossier.structured_data,
                "last_updated": updated_dossier.last_updated.isoformat() if updated_dossier.last_updated else None
            }
        )
    
    return updated_dossier


@router.put("/{dossier_id}/manual", response_model=dossier_schemas.Dossier)
async def update_dossier_manually(
    dossier_id: int,
    manual_update: dossier_schemas.DossierManualUpdate,
    db: Session = Depends(get_db)
):
    """Ручное обновление полей досье с отметкой о ручном изменении"""
    
    # Получаем существующее досье
    dossier = DossierService.get_dossier(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Досье не найдено")
    
    # Получаем текущие данные досье
    current_data = dossier.structured_data or {}
    client_info = current_data.get("client_info", {})
    manual_modifications = current_data.get("manual_modifications", {})
    
    # Обновляем только те поля, которые переданы и действительно изменились
    update_data = manual_update.model_dump(exclude_unset=True)
    current_time = datetime.utcnow().isoformat()  
    
    for field, new_value in update_data.items():
        if new_value is not None:  # Обновляем только если значение передано
            existing_value = client_info.get(field, "")
            
            # Нормализуем значения для сравнения
            normalized_existing = existing_value if existing_value is not None else ""
            normalized_new = new_value if new_value is not None else ""
            
            # Если значение действительно изменилось
            if normalized_existing != normalized_new:
                client_info[field] = new_value
                manual_modifications[field] = {
                    "modified_at": current_time,
                    "modified_by": "human"
                }
    
    # Формируем обновленную структуру данных
    new_structured_data = {
        **current_data,
        "client_info": client_info,
        "manual_modifications": manual_modifications
    }
    
    # Обновляем досье
    dossier_update = dossier_schemas.DossierUpdate(structured_data=new_structured_data)
    updated_dossier = DossierService.update_dossier(db, dossier_id, dossier_update)
    if updated_dossier:
        # Уведомляем фронтенд об обновлении
        await notify_dossier_update(
            client_id=updated_dossier.client_id,
            dossier_data={
                "id": updated_dossier.id,
                "client_id": updated_dossier.client_id,
                "structured_data": updated_dossier.structured_data,
                "last_updated": updated_dossier.last_updated.isoformat() if updated_dossier.last_updated else None
            }
        )
    
    return updated_dossier


@router.put("/client/{client_id}/manual", response_model=dossier_schemas.Dossier)
async def update_dossier_manually_by_client(
    client_id: int,
    manual_update: dossier_schemas.DossierManualUpdate,
    db: Session = Depends(get_db)
):
    """Ручное обновление полей досье клиента с отметкой о ручном изменении"""
    
    # Проверяем, что клиент существует
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Получаем или создаем досье
    dossier = DossierService.get_dossier_by_client(db, client_id)
    if not dossier:
        # Создаем новое досье если его нет
        dossier_create = dossier_schemas.DossierCreate(
            client_id=client_id,
            structured_data={"client_info": {}, "manual_modifications": {}}
        )
        dossier = DossierService.create_dossier(db, dossier_create)
    
    # Используем endpoint обновления по ID досье
    return await update_dossier_manually(dossier.id, manual_update, db)