import json
import time
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.database import SessionLocal
from ..services.message_service import MessageService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Создаем копию списка для безопасной итерации
        connections_to_remove = []
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message)
            except:
                # Соединение закрыто, помечаем для удаления
                connections_to_remove.append(connection)
        
        # Удаляем неактивные соединения после итерации
        for connection in connections_to_remove:
            if connection in self.active_connections:
                self.active_connections.remove(connection)


manager = ConnectionManager()


@router.websocket("/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket: Новое подключение...")
    await manager.connect(websocket)
    logger.info("WebSocket: Подключение принято")
    
    # Отправляем приветственное сообщение сразу после подключения
    welcome_message = json.dumps({"type": "welcome", "message": "Connected to dashboard", "timestamp": str(int(time.time()))})
    await websocket.send_text(welcome_message)
    logger.info("WebSocket: Приветственное сообщение отправлено")
    
    try:
        while True:
            logger.info("WebSocket: Ожидание сообщения...")
            # Ожидаем сообщения от клиента
            data = await websocket.receive_text()
            logger.info(f"WebSocket: Получено сообщение: {data}")
            
            try:
                # Парсим JSON сообщение
                message = json.loads(data)
                message_type = message.get("type", "")
                
                # Обрабатываем пинг-сообщения
                if message_type == "ping":
                    pong_response = json.dumps({"type": "pong", "timestamp": str(int(time.time()))})
                    await websocket.send_text(pong_response)
                elif message_type == "connect":
                    # Отправляем подтверждение подключения
                    connect_response = json.dumps({"type": "connected", "timestamp": str(int(time.time()))})
                    await websocket.send_text(connect_response)
                    logger.info(f"WebSocket клиент подключен")
                else:
                    # Обрабатываем другие типы сообщений
                    logger.info(f"Получено WebSocket сообщение: {message}")
                    
            except json.JSONDecodeError:
                # Если не JSON, считаем это пингом
                await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception as e:
                logger.error(f"Ошибка обработки WebSocket сообщения: {e}")
            
    except WebSocketDisconnect:
        logger.info("WebSocket: Клиент отключился")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket ошибка: {e}")
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
    logger.info(f"WebSocket: Отправляем уведомление о досье для клиента {client_id}")
    logger.info(f"WebSocket: Данные досье: {dossier_data}")
    
    message = json.dumps({
        "type": "dossier_update",
        "client_id": client_id,
        "data": dossier_data
    })
    
    logger.info(f"WebSocket: Уведомление отправляется {len(manager.active_connections)} активным соединениям")
    await manager.broadcast(message)
    logger.info(f"WebSocket: Уведомление о досье отправлено")


async def notify_car_interest_update(client_id: int, car_interest_data: dict):
    """Функция для уведомления о обновлении автомобильных интересов"""
    logger.info(f"WebSocket: Отправляем уведомление о автомобильных интересах для клиента {client_id}")
    logger.info(f"WebSocket: Данные автомобильных интересов: {car_interest_data}")
    
    message = json.dumps({
        "type": "car_interest_update",
        "client_id": client_id,
        "data": car_interest_data
    })
    
    logger.info(f"WebSocket: Уведомление отправляется {len(manager.active_connections)} активным соединениям")
    await manager.broadcast(message)
    logger.info(f"WebSocket: Уведомление о автомобильных интересах отправлено")


async def notify_task_update(client_id: int, task_data: dict):
    """Функция для уведомления о обновлении задач"""
    logger.info(f"WebSocket: Отправляем уведомление о задачах для клиента {client_id}")
    logger.info(f"WebSocket: Данные задач: {task_data}")
    
    message = json.dumps({
        "type": "task_update",
        "client_id": client_id,
        "data": task_data
    })
    
    logger.info(f"WebSocket: Уведомление отправляется {len(manager.active_connections)} активным соединениям")
    await manager.broadcast(message)
    logger.info(f"WebSocket: Уведомление о задачах отправлено")