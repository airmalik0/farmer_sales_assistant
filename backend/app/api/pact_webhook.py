from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..core.database import get_db, SessionLocal
from ..services.client_service import ClientService
from ..services.message_service import MessageService
from ..services.telegram_admin_service import TelegramAdminService
from ..services.ai import ClientAnalysisWorkflow
from .websocket import notify_new_message, notify_new_client
from ..core.config import settings
from ..models.message import Message
import json
import hmac
import hashlib
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

webhook_retry_queue = []

@router.post("/webhook/pact")
async def handle_pact_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        # Получаем тело запроса
        body = await request.body()
        webhook_data = json.loads(body.decode())
        
        logger.info(f"Получен Pact webhook: {webhook_data}")
        
        # Проверяем подпись только если секрет настроен
        if settings.pact_webhook_secret:
            signature = request.headers.get('X-Pact-Signature')
            if not signature or not _verify_webhook_signature(body, signature):
                logger.warning("Неверная подпись Pact webhook")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Определяем тип события - поддерживаем разные форматы
        event_type = webhook_data.get('type')
        event_action = webhook_data.get('event')
        
        # Получаем данные из разных возможных полей
        data = webhook_data.get('object') or webhook_data.get('data')
        
        try:
            # Обрабатываем разные типы событий
            if event_type == 'conversation':
                await _handle_conversation_webhook(db, event_action, data)
            elif event_type == 'message':
                await _handle_message_webhook(db, event_action, data, webhook_data)
            elif event_type == 'job':
                await _handle_job_webhook(db, event_action, data)
            elif event_type == 'auth':
                await _handle_auth_webhook(event_action, data)
            else:
                logger.info(f"Неизвестный тип webhook: {event_type}, действие: {event_action}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            # Добавляем в очередь для повторной попытки
            background_tasks.add_task(
                schedule_webhook_retry, 
                webhook_data, 
                retry_count=1
            )
            
        return {"status": "ok"}
        
    except json.JSONDecodeError:
        logger.error("Не удалось распарсить JSON webhook'а")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Критическая ошибка webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def schedule_webhook_retry(webhook_data: dict, retry_count: int, max_retries: int = 3):
    """Повторная обработка webhook'а с экспоненциальной задержкой"""
    if retry_count > max_retries:
        logger.error(f"Достигнуто максимальное количество попыток для webhook: {webhook_data}")
        await TelegramAdminService.send_notification(
            f"❌ Ошибка обработки Pact webhook после {max_retries} попыток"
        )
        return
    
    delay = min(2 ** retry_count, 60)  # Максимум 60 секунд
    await asyncio.sleep(delay)
    
    try:
        db = SessionLocal()
        try:
            event_type = webhook_data.get('type')
            event_action = webhook_data.get('event')
            data = webhook_data.get('object') or webhook_data.get('data')
            
            if event_type == 'conversation':
                await _handle_conversation_webhook(db, event_action, data)
            elif event_type == 'message':
                await _handle_message_webhook(db, event_action, data, webhook_data)
            elif event_type == 'job':
                await _handle_job_webhook(db, event_action, data)
                
            logger.info(f"Успешно обработан webhook на попытке {retry_count}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Ошибка повторной обработки webhook (попытка {retry_count}): {e}")
        await schedule_webhook_retry(webhook_data, retry_count + 1, max_retries)


async def _handle_conversation_webhook(db: Session, event: str, conversation_data: Dict[str, Any]):
    """Обработка webhook'ов разговоров"""
    logger.info(f"Получен conversation webhook - event: {event}, data: {conversation_data}")
    
    if not conversation_data:
        logger.warning("Пустые данные в conversation webhook")
        return
        
    conversation_id = conversation_data.get('id')  # В реальной структуре Pact это просто 'id'
    if not conversation_id:
        logger.warning(f"Отсутствует id в conversation webhook: {conversation_data}")
        return
    
    logger.info(f"Обрабатываем {event} conversation: {conversation_id}")
    
    try:
        # Ищем существующего клиента
        client = ClientService.find_client_by_pact_conversation(db, conversation_id)
        
        # Если клиента нет — создаём его и на update-событии тоже
        if not client and event in ['create', 'new', 'update']:
            client = ClientService.create_client_from_pact_conversation(db, conversation_data)
            logger.info(f"Создан новый клиент: {client.id} (event={event})")
            
            # Уведомляем админа
            await TelegramAdminService.send_new_client_notification(client)
            
            # Отправляем WebSocket уведомление о новом клиенте
            await notify_new_client({
                "client_id": client.id,
                "provider": client.provider,
                "name": client.name
            })
        
        # Если клиент есть — обновляем на update
        elif event == 'update' and client:
            client = ClientService.update_client_from_pact(db, client, conversation_data)
            logger.info(f"Обновлен клиент: {client.id}")
            
    except Exception as e:
        logger.error(f"Ошибка обработки conversation webhook: {e}")
        raise


async def _handle_message_webhook(db: Session, event: str, message_data: Dict[str, Any], full_webhook: Dict[str, Any]):
    """Обработка webhook'ов сообщений"""
    logger.info(f"Получен message webhook - event: {event}, data: {message_data}, full: {full_webhook}")
    
    if not message_data:
        logger.warning("Пустые данные в message webhook")
        return
    
    # В реальных вебхуках conversation_id находится прямо в объекте message
    conversation_id = message_data.get('conversation_id')
    
    # Эффективный ID сообщения: берем id, либо external_id (в "new" событиях)
    effective_message_id = message_data.get('id') or message_data.get('external_id')
    
    if not conversation_id:
        logger.warning("Отсутствует conversation_id в message webhook")
        return
        
    logger.info(f"Обрабатываем {event} message: {effective_message_id} в conversation: {conversation_id}")
    
    try:
        # Ищем клиента
        client = ClientService.find_client_by_pact_conversation(db, conversation_id)
        if not client:
            # Клиент ещё не создан (например, придет позже conversation update) — инициируем ретрай через верхний обработчик
            raise Exception(f"Клиент не найден для conversation_id: {conversation_id}")
        
        # Если у нас нет id в данных (например, для event=new), проставим его из effective_message_id
        if effective_message_id and not message_data.get('id'):
            message_data = dict(message_data)
            message_data['id'] = int(effective_message_id)
        
        if event in ['create', 'new']:
            # Проверяем, не существует ли уже это сообщение
            if effective_message_id:
                existing_message = MessageService.find_message_by_pact_id(db, int(effective_message_id))
                if existing_message:
                    logger.info(f"Сообщение {effective_message_id} уже существует, пропускаем")
                    return
            
            # Создаем новое сообщение
            message = MessageService.create_message_from_pact(db, client.id, message_data)
            logger.info(f"Создано сообщение: {message.id}")
            
            # Обновляем contact_id клиента если он еще не установлен
            if client.pact_contact_id is None and message_data.get('contact_id'):
                client.pact_contact_id = message_data.get('contact_id')
                db.commit()
            
            # Обновляем информацию о последнем сообщении клиента
            ClientService.update_last_message_info(db, client.id, message.pact_message_id)
            
            # Отправляем WebSocket уведомление
            await notify_new_message({
                "client_id": client.id,
                "message_id": message.id,
                "content": message.content,
                "sender": message.sender.value
            })
            
            # Запускаем AI анализ для входящих сообщений
            if message.sender.value == 'client':
                try:
                    # Планируем анализ клиента с небольшой задержкой
                    ClientAnalysisWorkflow.schedule_analysis_after_delay(message.client_id, delay_minutes=0.1)
                except Exception as e:
                    logger.error(f"Ошибка AI анализа сообщения {message.id}: {e}")
            
        elif event == 'update' and effective_message_id:
            # Обновляем существующее сообщение или создаем, если его еще нет
            message = MessageService.find_message_by_pact_id(db, int(effective_message_id))
            if message:
                message = MessageService.update_message_from_pact(db, message, message_data)
                logger.info(f"Обновлено сообщение: {message.id}")
            else:
                # Сообщение отсутствует (скорее всего create/new пришли раньше без клиента) — создаем его сейчас
                message = MessageService.create_message_from_pact(db, client.id, message_data)
                logger.info(f"Создано сообщение (по update): {message.id}")
                
                # Отправляем WebSocket уведомление о новом сообщении
                await notify_new_message({
                    "client_id": client.id,
                    "message_id": message.id,
                    "content": message.content,
                    "sender": message.sender.value
                })
                
    except Exception as e:
        logger.error(f"Ошибка обработки message webhook: {e}")
        raise


async def _handle_job_webhook(db: Session, event: str, job_data: Dict[str, Any]):
    """Обработка webhook'ов выполнения задач"""
    if not job_data or event != 'executed':
        return
        
    message_id = job_data.get('message_id')
    result = job_data.get('result')
    
    if not message_id:
        return
        
    logger.info(f"Job executed for message {message_id}: {result}")
    
    try:
        # Обновляем статус сообщения на основе результата выполнения
        message = MessageService.find_message_by_pact_id(db, int(message_id))
        if message:
            # Преобразуем результат job'а в статус сообщения
            status_mapping = {
                'DELIVERED': 'delivered',
                'READ': 'read',
                'FAILED': 'error'
            }
            
            new_status = status_mapping.get(result, message.status)
            if new_status != message.status:
                message.status = new_status
                db.commit()
                logger.info(f"Обновлен статус сообщения {message.id}: {new_status}")
                
    except Exception as e:
        logger.error(f"Ошибка обработки job webhook: {e}")


async def _handle_auth_webhook(event: str, auth_data: Dict[str, Any]):
    """Обработка webhook'ов аутентификации"""
    logger.info(f"Auth webhook: {event}")
    
    if event == 'failed':
        await TelegramAdminService.send_notification(
            "❌ Ошибка аутентификации Pact API"
        )
    elif event == 'success':
        await TelegramAdminService.send_notification(
            "✅ Успешная аутентификация Pact API"
        )


def _verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Проверка подписи webhook'а"""
    if not settings.pact_webhook_secret:
        return True  # Если секрет не настроен, пропускаем проверку
        
    try:
        expected_signature = hmac.new(
            settings.pact_webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    except Exception as e:
        logger.error(f"Ошибка проверки подписи: {e}")
        return False


@router.post("/pact/send")
async def send_pact_message(
    request: Request,
    db: Session = Depends(get_db)
):
    """Отправить сообщение через Pact API"""
    try:
        # Получаем JSON из тела запроса
        body = await request.json()
        client_id = body.get('client_id')
        content = body.get('content')
        content_type = body.get('content_type', 'text')
        
        if not client_id or not content:
            raise HTTPException(status_code=400, detail="Требуется client_id и content")
        
        # Получаем клиента
        client = ClientService.get_client(db, client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        
        if not client.pact_conversation_id:
            raise HTTPException(
                status_code=400, 
                detail="У клиента нет pact_conversation_id. Возможно клиент создан не через Pact"
            )
        
        # Импортируем здесь чтобы избежать циклических импортов
        from ..services.pact_service import PactService
        
        # Отправляем сообщение через Pact API V2
        result = await PactService.send_message_to_conversation(
            conversation_id=client.pact_conversation_id,
            text=content
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Не удалось отправить сообщение через Pact")
        
        # Создаем запись о сообщении в БД (API V2 возвращает объект message)
        # API V2 возвращает структуру {"message": {...}}
        message_obj = result.get('message', result)
        message_data = {
            'id': message_obj.get('id'),
            'conversation_id': client.pact_conversation_id,
            'message': content,  # В API V2 поле называется message
            'income': False,  # Исходящее сообщение
            'status': message_obj.get('status', 'sent'),
            'contact_id': message_obj.get('contact_id')
        }
        
        message = MessageService.create_message_from_pact(db, client_id, message_data)
        
        # Уведомляем через WebSocket
        await notify_new_message({
            "client_id": client_id,
            "message_id": message.id,
            "content": content,
            "sender": "assistant",
            "event": "message_sent"
        })
        
        return {
            "success": True,
            "message_id": message.id,
            "pact_message_id": message_obj.get('id')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения через Pact: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 