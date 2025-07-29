from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas import client as client_schemas
from ..services.client_service import ClientService

router = APIRouter()


@router.get("/", response_model=List[client_schemas.Client])
def get_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех клиентов"""
    clients = ClientService.get_clients(db, skip=skip, limit=limit)
    return clients


@router.get("/{client_id}", response_model=client_schemas.Client)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Получить клиента по ID"""
    client = ClientService.get_client(db, client_id=client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@router.get("/telegram/{telegram_id}", response_model=client_schemas.Client)
def get_client_by_telegram_id(telegram_id: int, db: Session = Depends(get_db)):
    """Получить клиента по Telegram ID"""
    client = ClientService.get_client_by_telegram_id(db, telegram_id=telegram_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@router.post("/", response_model=client_schemas.Client)
def create_client(client: client_schemas.ClientCreate, db: Session = Depends(get_db)):
    """Создать нового клиента"""
    existing_client = ClientService.get_client_by_telegram_id(db, telegram_id=client.telegram_id)
    if existing_client:
        raise HTTPException(status_code=400, detail="Клиент с таким Telegram ID уже существует")
    return ClientService.create_client(db=db, client=client)


@router.put("/{client_id}", response_model=client_schemas.Client)
def update_client(
    client_id: int, 
    client_update: client_schemas.ClientUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить данные клиента"""
    client = ClientService.update_client(db, client_id=client_id, client_update=client_update)
    if client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@router.post("/{client_id}/approve-name", response_model=client_schemas.Client)
def approve_client_name(client_id: int, db: Session = Depends(get_db)):
    """Одобрить имя клиента для рассылки"""
    client = ClientService.get_client(db, client_id=client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Проверяем что у клиента есть имя
    if not client.first_name:
        raise HTTPException(status_code=400, detail="У клиента должно быть указано имя для одобрения")
    
    # Одобряем имя
    client_update = client_schemas.ClientUpdate(name_approved=True)
    updated_client = ClientService.update_client(db, client_id=client_id, client_update=client_update)
    return updated_client