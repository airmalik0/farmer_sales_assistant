from openai import OpenAI
from typing import List
from datetime import datetime, timedelta
from celery import current_app
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import SessionLocal
from ..core.celery import celery_app
from ..models.message import Message
from ..models.client import Client
from .message_service import MessageService
from .dossier_service import DossierService

client = OpenAI(api_key=settings.openai_api_key)


class AIService:
    @staticmethod
    def format_chat_history(messages: List[Message]) -> str:
        """Форматирует историю чата для анализа AI"""
        formatted_messages = []
        for msg in messages:
            sender = "Клиент" if msg.sender.value == "client" else "Менеджер"
            content = msg.content
            
            # Добавляем информацию о типе контента
            if msg.content_type != "text":
                content = f"[{msg.content_type.upper()}] {content}"
            
            formatted_messages.append(f"{sender}: {content}")
        
        return "\n".join(formatted_messages)

    @staticmethod
    def generate_dossier_prompt(chat_history: str, client_name: str) -> str:
        """Создает промпт для генерации досье клиента"""
        return f"""
Ты - аналитик CRM-системы. Проанализируй переписку с клиентом {client_name} и составь краткое досье.

История переписки:
{chat_history}

Составь тезисное досье клиента, включающее:
1. Основные потребности и интересы
2. Стиль общения и предпочтения
3. Ключевые обсужденные темы
4. Этап в воронке продаж
5. Рекомендации по дальнейшему общению

Досье должно быть кратким (до 500 слов) и практичным для менеджера по продажам.
"""

    @staticmethod
    def generate_dossier(chat_history: str, client_name: str) -> str:
        """Генерирует досье клиента с помощью OpenAI"""
        try:
            prompt = AIService.generate_dossier_prompt(chat_history, client_name)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты эксперт по анализу клиентского взаимодействия."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Ошибка при генерации досье: {e}")
            return f"Ошибка анализа: {str(e)}"

    @staticmethod
    def check_inactive_chats() -> List[int]:
        """Находит чаты, неактивные в течение 5 минут"""
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            
            # Находим клиентов с последним сообщением старше 5 минут
            subquery = (db.query(Message.client_id, Message.timestamp)
                       .order_by(Message.client_id, Message.timestamp.desc())
                       .distinct(Message.client_id)
                       .subquery())
            
            inactive_client_ids = (db.query(subquery.c.client_id)
                                  .filter(subquery.c.timestamp < cutoff_time)
                                  .all())
            
            return [client_id[0] for client_id in inactive_client_ids]
        finally:
            db.close()


@celery_app.task
def analyze_client_dialogue(client_id: int):
    """Celery задача для анализа диалога клиента"""
    db = SessionLocal()
    try:
        # Получаем клиента
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return f"Клиент {client_id} не найден"

        # Получаем историю чата
        messages = MessageService.get_chat_history(db, client_id)
        if not messages:
            return f"Нет сообщений для клиента {client_id}"

        # Форматируем историю
        chat_history = AIService.format_chat_history(messages)
        client_name = client.first_name or f"ID {client.telegram_id}"

        # Генерируем досье
        summary = AIService.generate_dossier(chat_history, client_name)

        # Сохраняем досье
        DossierService.update_or_create_dossier(db, client_id, summary)
        
        return f"Досье для клиента {client_name} обновлено"
    
    except Exception as e:
        return f"Ошибка при анализе диалога клиента {client_id}: {str(e)}"
    finally:
        db.close()


@celery_app.task
def check_and_analyze_inactive_chats():
    """Периодическая задача для проверки неактивных чатов"""
    inactive_client_ids = AIService.check_inactive_chats()
    
    for client_id in inactive_client_ids:
        # Запускаем анализ для каждого неактивного клиента
        analyze_client_dialogue.delay(client_id)
    
    return f"Запущен анализ для {len(inactive_client_ids)} неактивных чатов"