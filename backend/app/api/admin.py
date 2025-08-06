from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.client_service import ClientService
from ..services.message_service import MessageService
from ..services.pact_service import PactService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """Получить статистику для админа"""
    try:
        # Статистика клиентов
        all_clients = ClientService.get_clients(db)
        whatsapp_clients = ClientService.get_clients_by_provider(db, "whatsapp")
        telegram_clients = ClientService.get_clients_by_provider(db, "telegram_personal")
        approved_clients = ClientService.get_approved_clients(db)
        
        # Статистика сообщений за сегодня
        today = datetime.utcnow().date()
        today_stats = MessageService.get_message_stats(db)
        
        # Попробуем проверить статус Pact API
        pact_status = "unknown"
        last_webhook = "never"
        
        try:
            pact_response = await PactService.get_conversations(page=1, per_page=1)
            pact_status = "connected" if pact_response else "error"
        except Exception as e:
            logger.error(f"Ошибка проверки Pact API: {e}")
            pact_status = "error"
        
        return {
            "clients": {
                "whatsapp": len(whatsapp_clients),
                "telegram_personal": len(telegram_clients), 
                "total": len(all_clients),
                "approved": len(approved_clients)
            },
            "messages": {
                "incoming": today_stats.get("incoming", 0),
                "outgoing": today_stats.get("outgoing", 0)
            },
            "pact": {
                "status": pact_status,
                "last_webhook": last_webhook
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")

@router.post("/sync-conversations")
async def sync_conversations(db: Session = Depends(get_db)):
    """Синхронизация бесед с Pact API"""
    try:
        total_conversations = 0
        created_clients = 0
        page = 1
        
        while True:
            # Получаем беседы из Pact API V2
            pact_response = await PactService.get_conversations(page=page, per_page=25)
            
            if not pact_response or not pact_response.get("conversations"):
                break
                
            conversations = pact_response["conversations"]
            total_conversations += len(conversations)
            
            for conversation_data in conversations:
                conversation_id = conversation_data["id"]
                
                # Проверяем, есть ли уже такой клиент
                existing_client = ClientService.find_client_by_pact_conversation(
                    db, conversation_id
                )
                
                if not existing_client:
                    # Создаем нового клиента
                    client = ClientService.create_client_from_pact_conversation(
                        db, conversation_data
                    )
                    created_clients += 1
                    logger.info(f"Создан клиент из беседы {conversation_id}")
                else:
                    # Обновляем существующего
                    ClientService.update_client_from_pact(
                        db, existing_client, conversation_data
                    )
            
            # Если получили меньше 25 бесед, значит это последняя страница
            if len(conversations) < 25:
                break
                
            page += 1
        
        return {
            "success": True,
            "total_conversations": total_conversations,
            "created_clients": created_clients
        }
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации с Pact: {e}")
        raise HTTPException(status_code=500, detail="Ошибка синхронизации с Pact")

@router.get("/test-pact")
async def test_pact_connection():
    """Тест подключения к Pact API"""
    try:
        response = await PactService.get_conversations(page=1, per_page=1)
        
        if response:
            return {
                "status": "success",
                "message": "Подключение к Pact API работает",
                "company_id": PactService.COMPANY_ID
            }
        else:
            return {
                "status": "error", 
                "message": "Не удалось подключиться к Pact API"
            }
            
    except Exception as e:
        logger.error(f"Ошибка тестирования Pact API: {e}")
        return {
            "status": "error",
            "message": f"Ошибка: {str(e)}"
        } 