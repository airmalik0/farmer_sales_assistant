from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..core.database import get_db
from ..services.client_service import ClientService
from ..services.message_service import MessageService
from ..services.settings_service import SettingsService
from ..schemas.message import MessageCreate
from .websocket import notify_new_message
import httpx
import os
import asyncio

router = APIRouter()

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


class SendMessageRequest(BaseModel):
    client_id: int
    content: str
    content_type: str = "text"


class BroadcastRequest(BaseModel):
    content: str
    content_type: str = "text"
    include_greeting: bool = True


async def send_telegram_message(chat_id: int, text: str):
    """Асинхронно отправляет текстовое сообщение через Telegram Bot API."""
    async with httpx.AsyncClient() as client:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Ошибка при отправке сообщения в Telegram: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Ошибка запроса к Telegram API: {e}")
            return None


async def send_telegram_voice(chat_id: int, voice_file_id: str):
    """Отправляет голосовое сообщение через Telegram Bot API."""
    async with httpx.AsyncClient() as client:
        url = f"{TELEGRAM_API_URL}/sendVoice"
        payload = {"chat_id": chat_id, "voice": voice_file_id}
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при отправке голосового сообщения: {e}")
            return None


async def send_telegram_video_note(chat_id: int, video_note_file_id: str):
    """Отправляет видео-кружок через Telegram Bot API."""
    async with httpx.AsyncClient() as client:
        url = f"{TELEGRAM_API_URL}/sendVideoNote"
        payload = {"chat_id": chat_id, "video_note": video_note_file_id}
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при отправке видео-кружка: {e}")
            return None


async def send_telegram_document(chat_id: int, document_file_id: str):
    """Отправляет документ через Telegram Bot API."""
    async with httpx.AsyncClient() as client:
        url = f"{TELEGRAM_API_URL}/sendDocument"
        payload = {"chat_id": chat_id, "document": document_file_id}
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при отправке документа: {e}")
            return None


async def send_telegram_photo(chat_id: int, photo_file_id: str):
    """Отправляет фото через Telegram Bot API."""
    async with httpx.AsyncClient() as client:
        url = f"{TELEGRAM_API_URL}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": photo_file_id}
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при отправке фото: {e}")
            return None


def extract_file_id(content: str, content_type: str) -> str:
    """Извлекает file_id из контента сообщения."""
    if content_type == "voice" and content.startswith("voice_file_id:"):
        return content.split("voice_file_id:")[1]
    elif content_type == "video_note" and content.startswith("video_note_file_id:"):
        return content.split("video_note_file_id:")[1]
    elif content_type == "document" and content.startswith("document_file_id:"):
        return content.split("document_file_id:")[1].split(",")[0]
    elif content_type == "photo" and content.startswith("photo_file_id:"):
        return content.split("photo_file_id:")[1]
    return ""


def replace_greeting_variables(greeting_text: str, first_name: str = "", last_name: str = "") -> str:
    """Заменяет переменные в тексте приветствия на реальные значения."""
    text = greeting_text
    text = text.replace("[Имя Клиента]", first_name or "")
    text = text.replace("[Фамилия Клиента]", last_name or "")
    return text.strip()


async def send_telegram_content(chat_id: int, content_type: str, content: str):
    """Универсальная функция отправки любого типа контента."""
    if content_type == "text":
        return await send_telegram_message(chat_id, content)
    elif content_type == "voice":
        file_id = extract_file_id(content, content_type)
        if file_id:
            return await send_telegram_voice(chat_id, file_id)
    elif content_type == "video_note":
        file_id = extract_file_id(content, content_type)
        if file_id:
            return await send_telegram_video_note(chat_id, file_id)
    elif content_type == "document":
        file_id = extract_file_id(content, content_type)
        if file_id:
            return await send_telegram_document(chat_id, file_id)
    elif content_type == "photo":
        file_id = extract_file_id(content, content_type)
        if file_id:
            return await send_telegram_photo(chat_id, file_id)
    
    return None


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
    
    # Отправляем WebSocket уведомление
    await notify_new_message({
        "id": message.id,
        "client_id": message.client_id,
        "sender": message.sender.value,
        "content_type": message.content_type,
        "content": message.content,
        "timestamp": message.timestamp.isoformat()
    })
    
    # Отправляем сообщение через Telegram
    telegram_response = await send_telegram_content(
        chat_id=client.telegram_id,
        content_type=request.content_type,
        content=request.content
    )
    
    if not telegram_response or not telegram_response.get("ok"):
        print(f"Не удалось отправить сообщение клиенту {client.id}")
    
    return {
        "success": True,
        "message": "Сообщение отправлено",
        "message_id": message.id
    }


class BroadcastValidationResponse(BaseModel):
    clients_without_names: list[dict]
    clients_with_unapproved_names: list[dict]
    total_clients: int
    clients_ready: int
    can_broadcast: bool


@router.get("/broadcast/validate")
def validate_broadcast_clients(db: Session = Depends(get_db)):
    """Проверяет клиентов перед рассылкой"""
    clients = ClientService.get_clients(db)
    
    if not clients:
        raise HTTPException(status_code=404, detail="Нет клиентов для рассылки")
    
    clients_without_names = []
    clients_with_unapproved_names = []
    clients_ready = 0
    
    for client in clients:
        if not client.first_name:
            # Клиенты без имени
            clients_without_names.append({
                "id": client.id,
                "telegram_id": client.telegram_id,
                "username": client.username,
                "name_approved": client.name_approved
            })
        elif not client.name_approved:
            # Клиенты с именем, но неодобренным
            clients_with_unapproved_names.append({
                "id": client.id,
                "telegram_id": client.telegram_id,
                "username": client.username,
                "first_name": client.first_name,
                "last_name": client.last_name,
                "name_approved": client.name_approved
            })
        else:
            # Клиенты готовые к рассылке
            clients_ready += 1
    
    # Рассылка возможна только если все клиенты одобрены
    can_broadcast = len(clients_without_names) == 0 and len(clients_with_unapproved_names) == 0
    
    return BroadcastValidationResponse(
        clients_without_names=clients_without_names,
        clients_with_unapproved_names=clients_with_unapproved_names,
        total_clients=len(clients),
        clients_ready=clients_ready,
        can_broadcast=can_broadcast
    )


@router.post("/broadcast")
async def broadcast_message(
    request: BroadcastRequest,
    db: Session = Depends(get_db)
):
    """Массовая рассылка всем клиентам"""
    # Проверяем валидацию перед рассылкой
    validation = validate_broadcast_clients(db)
    if not validation.can_broadcast:
        raise HTTPException(
            status_code=400, 
            detail=f"Невозможно начать рассылку. Клиентов без имени: {len(validation.clients_without_names)}, с неодобренными именами: {len(validation.clients_with_unapproved_names)}"
        )
    
    # Получаем всех клиентов
    clients = ClientService.get_clients(db)
    
    if not clients:
        raise HTTPException(status_code=404, detail="Нет клиентов для рассылки")
    
    sent_count = 0
    failed_count = 0
    
    for client in clients:
        try:
            # Персонализированное приветствие (если включено)
            if request.include_greeting:
                # Получаем эффективное приветствие из БД
                effective_greeting = SettingsService.get_effective_greeting(db)
                
                # Заменяем переменные в приветствии
                greeting = replace_greeting_variables(
                    effective_greeting,
                    client.first_name or "",
                    client.last_name or ""
                )
                
                # Сохраняем приветствие в базе
                greeting_data = MessageCreate(
                    client_id=client.id,
                    sender="farmer",
                    content_type="text",
                    content=greeting
                )
                greeting_message = MessageService.create_message(db, greeting_data)
                
                # Отправляем приветствие
                greeting_response = await send_telegram_message(client.telegram_id, greeting)
                
                # Уведомляем фронтенд о приветствии
                await notify_new_message({
                    "id": greeting_message.id,
                    "client_id": greeting_message.client_id,
                    "sender": greeting_message.sender.value,
                    "content_type": greeting_message.content_type,
                    "content": greeting_message.content,
                    "timestamp": greeting_message.timestamp.isoformat()
                })
                
                # Небольшая задержка между приветствием и основным сообщением
                await asyncio.sleep(0.1)
            
            # Основное сообщение - сохраняем в базе
            message_data = MessageCreate(
                client_id=client.id,
                sender="farmer",
                content_type=request.content_type,
                content=request.content
            )
            message = MessageService.create_message(db, message_data)
            
            # Отправляем основное сообщение
            telegram_response = await send_telegram_content(
                chat_id=client.telegram_id,
                content_type=request.content_type,
                content=request.content
            )
            
            # Уведомляем фронтенд об основном сообщении
            await notify_new_message({
                "id": message.id,
                "client_id": message.client_id,
                "sender": message.sender.value,
                "content_type": message.content_type,
                "content": message.content,
                "timestamp": message.timestamp.isoformat()
            })
            
            if telegram_response and telegram_response.get("ok"):
                sent_count += 1
            else:
                failed_count += 1
                print(f"Не удалось отправить сообщение клиенту {client.id}")
            
            # Задержка между сообщениями
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Ошибка при отправке сообщения клиенту {client.id}: {e}")
            failed_count += 1
    
    return {
        "success": True,
        "message": f"Рассылка завершена. Отправлено: {sent_count}, не удалось: {failed_count}",
        "sent_count": sent_count,
        "failed_count": failed_count,
        "total_clients": len(clients)
    }


@router.get("/media/{file_id}")
async def get_media_file(file_id: str):
    """Получить медиафайл из Telegram и вернуть его как response"""
    from fastapi.responses import StreamingResponse
    import io
    
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Telegram bot token не настроен")
    
    try:
        # Получаем информацию о файле из Telegram
        async with httpx.AsyncClient() as client:
            get_file_url = f"{TELEGRAM_API_URL}/getFile"
            params = {"file_id": file_id}
            
            response = await client.get(get_file_url, params=params)
            response.raise_for_status()
            
            file_info = response.json()
            if not file_info.get("ok"):
                raise HTTPException(status_code=404, detail="Файл не найден в Telegram")
            
            file_path = file_info["result"]["file_path"]
            
            # Скачиваем файл
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            file_response = await client.get(download_url)
            file_response.raise_for_status()
            
            # Определяем MIME-тип на основе расширения файла
            file_extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg', 
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'mp4': 'video/mp4',
                'webm': 'video/webm',
                'ogg': 'audio/ogg',
                'oga': 'audio/ogg',
                'mp3': 'audio/mpeg',
                'wav': 'audio/wav',
                'pdf': 'application/pdf',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'txt': 'text/plain'
            }
            
            content_type = mime_types.get(file_extension, 'application/octet-stream')
            
            # Возвращаем файл как поток
            return StreamingResponse(
                io.BytesIO(file_response.content),
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",  # Кэшируем на час
                    "Content-Disposition": f"inline; filename=telegram_file.{file_extension}"
                }
            )
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Файл не найден")
        raise HTTPException(status_code=500, detail="Ошибка при получении файла из Telegram")
    except Exception as e:
        print(f"Ошибка при получении медиафайла: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
