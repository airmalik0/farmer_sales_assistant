import json
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.database import SessionLocal
from ..services.message_service import MessageService

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Соединение закрыто, удаляем его
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Ожидаем сообщения от клиента (пинг для поддержания соединения)
            data = await websocket.receive_text()
            # Можно обработать входящие команды от фронтенда
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def notify_new_message(message_data: dict):
    """Функция для уведомления всех подключенных клиентов о новом сообщении"""
    message = json.dumps({
        "type": "new_message",
        "data": message_data
    })
    await manager.broadcast(message)


async def notify_dossier_update(client_id: int, dossier_data: dict):
    """Функция для уведомления о обновлении досье"""
    message = json.dumps({
        "type": "dossier_update",
        "client_id": client_id,
        "data": dossier_data
    })
    await manager.broadcast(message)