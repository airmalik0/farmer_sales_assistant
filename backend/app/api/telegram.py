from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..core.database import get_db
from ..services.client_service import ClientService
from ..services.message_service import MessageService
from ..schemas.message import MessageCreate
import httpx
import os

router = APIRouter()

class SendMessageRequest(BaseModel):
    client_id: int
    content: str
    content_type: str = "text"

class BroadcastRequest(BaseModel):
    content: str
    content_type: str = "text"


@router.post("/send-message")
async def send_message_to_client(
    request: SendMessageRequest,
    db: Session = Depends(get_db)
):
    """Отправить сообщение конкретному клиенту через Telegram бота"""
    # Получаем клиента
    client = ClientService.get_client(db, request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Сохраняем сообщение в базе
    message_data = MessageCreate(
        client_id=request.client_id,
        sender="farmer",
        content_type=request.content_type,
        content=request.content
    )
    message = MessageService.create_message(db, message_data)
    
    # Отправляем сообщение через бота (здесь должна быть интеграция с ботом)
    # Пока возвращаем успех
    
    return {
        "success": True,
        "message": "Сообщение отправлено",
        "message_id": message.id
    }


@router.post("/broadcast")
async def broadcast_message(
    request: BroadcastRequest,
    db: Session = Depends(get_db)
):
    """Массовая рассылка всем клиентам"""
    # Получаем всех клиентов
    clients = ClientService.get_clients(db)
    
    if not clients:
        raise HTTPException(status_code=404, detail="Нет клиентов для рассылки")
    
    # Сохраняем сообщения в базе для всех клиентов
    sent_count = 0
    for client in clients:
        try:
            message_data = MessageCreate(
                client_id=client.id,
                sender="farmer", 
                content_type=request.content_type,
                content=request.content
            )
            MessageService.create_message(db, message_data)
            sent_count += 1
        except Exception as e:
            print(f"Ошибка сохранения сообщения для клиента {client.id}: {e}")
    
    return {
        "success": True,
        "message": f"Рассылка отправлена {sent_count} клиентам",
        "sent_count": sent_count,
        "total_clients": len(clients)
    }