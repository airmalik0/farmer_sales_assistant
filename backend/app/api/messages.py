from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas import message as message_schemas
from ..services.message_service import MessageService
from ..services.client_service import ClientService
from ..services.ai import ClientAnalysisWorkflow
from .websocket import notify_new_message
import asyncio

router = APIRouter()


@router.get("/", response_model=List[message_schemas.Message])
def get_recent_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить последние сообщения"""
    messages = MessageService.get_recent_messages(db, skip=skip, limit=limit)
    return messages


@router.get("/client/{client_id}", response_model=List[message_schemas.Message])
def get_messages_by_client(
    client_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Получить сообщения клиента"""
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    messages = MessageService.get_messages_by_client(db, client_id=client_id, skip=skip, limit=limit)
    return messages


@router.get("/{message_id}", response_model=message_schemas.Message)
def get_message(message_id: int, db: Session = Depends(get_db)):
    """Получить сообщение по ID"""
    message = MessageService.get_message(db, message_id=message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    return message


@router.post("/", response_model=message_schemas.Message)
async def create_message(message: message_schemas.MessageCreate, db: Session = Depends(get_db)):
    """Создать новое сообщение"""
    # Проверяем, что клиент существует
    client = ClientService.get_client(db, message.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Создаем сообщение
    created_message = MessageService.create_message(db=db, message=message)
    
    # Отправляем WebSocket уведомление
    await notify_new_message({
        "id": created_message.id,
        "client_id": created_message.client_id,
        "sender": created_message.sender.value,
        "content_type": created_message.content_type,
        "content": created_message.content,
        "created_at": created_message.created_at.isoformat()
    })
    
    # Запускаем анализ через 1 минуту после любого сообщения
    ClientAnalysisWorkflow.schedule_analysis_after_delay(message.client_id, delay_minutes=0.1)
    
    return created_message


@router.put("/{message_id}", response_model=message_schemas.Message)
def update_message(
    message_id: int, 
    message_update: message_schemas.MessageUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить сообщение"""
    message = MessageService.update_message(db, message_id=message_id, message_update=message_update)
    if message is None:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    return message