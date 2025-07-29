import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
from ..core.config import settings
from ..models.task import Task
from ..models.client import Client
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Telegram Bot API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


class TelegramService:
    
    @staticmethod
    async def send_message(chat_id: int, text: str) -> Optional[Dict[str, Any]]:
        """Отправляет текстовое сообщение через Telegram Bot API"""
        async with httpx.AsyncClient() as client:
            url = f"{TELEGRAM_API_URL}/sendMessage"
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Ошибка отправки сообщения в Telegram: {e.response.text}")
                return None
            except httpx.RequestError as e:
                logger.error(f"Ошибка запроса к Telegram API: {e}")
                return None

    @staticmethod
    async def send_task_notification_to_farmer(task: Task, client: Client) -> bool:
        """Отправляет уведомление фермеру о новой задаче"""
        if not settings.farmer_telegram_id:
            logger.warning("FARMER_TELEGRAM_ID не установлен")
            return False
        
        # Формируем сообщение
        client_name = f"{client.first_name or ''} {client.last_name or ''}".strip()
        if not client_name:
            client_name = client.username or f"ID:{client.telegram_id}"
        
        priority_emoji = {
            "low": "🔵",
            "normal": "🟡", 
            "high": "🔴"
        }.get(task.priority, "⚪")
        
        due_date_text = ""
        if task.due_date:
            due_date_text = f"\n📅 <b>Срок:</b> {task.due_date.strftime('%d.%m.%Y')}"
        
        source_text = ""
        if task.source == "trigger":
            source_text = "\n🤖 <b>Источник:</b> Триггер"
        elif task.source == "ai":
            source_text = "\n🧠 <b>Источник:</b> AI анализ"
        
        message = f"""
{priority_emoji} <b>Новая задача</b>

👤 <b>Клиент:</b> {client_name}
📝 <b>Описание:</b> {task.description}{due_date_text}{source_text}

🆔 <b>ID задачи:</b> {task.id}
""".strip()
        
        result = await TelegramService.send_message(
            chat_id=settings.farmer_telegram_id,
            text=message
        )
        
        if result:
            logger.info(f"Уведомление о задаче {task.id} отправлено фермеру")
            return True
        else:
            logger.error(f"Не удалось отправить уведомление о задаче {task.id}")
            return False

    @staticmethod
    async def send_task_reminder_to_farmer(task: Task, client: Client) -> bool:
        """Отправляет напоминание фермеру о просроченной задаче"""
        if not settings.farmer_telegram_id:
            logger.warning("FARMER_TELEGRAM_ID не установлен")
            return False
        
        client_name = f"{client.first_name or ''} {client.last_name or ''}".strip()
        if not client_name:
            client_name = client.username or f"ID:{client.telegram_id}"
        
        message = f"""
⏰ <b>Напоминание о задаче</b>

👤 <b>Клиент:</b> {client_name}
📝 <b>Описание:</b> {task.description}
📅 <b>Срок был:</b> {task.due_date.strftime('%d.%m.%Y')}

❗ Задача просрочена!
🆔 <b>ID задачи:</b> {task.id}
""".strip()
        
        result = await TelegramService.send_message(
            chat_id=settings.farmer_telegram_id,
            text=message
        )
        
        if result:
            logger.info(f"Напоминание о задаче {task.id} отправлено фермеру")
            return True
        else:
            logger.error(f"Не удалось отправить напоминание о задаче {task.id}")
            return False

    @staticmethod
    async def send_trigger_notification_to_farmer(
        trigger_name: str,
        car_data: Dict[str, Any],
        formatted_message: str
    ) -> bool:
        """Отправляет уведомление фермеру о срабатывании триггера"""
        if not settings.farmer_telegram_id:
            logger.warning("FARMER_TELEGRAM_ID не установлен")
            return False
        
        car_id = car_data.get('car_id', 'N/A')
        brand = car_data.get('brand', 'N/A')
        model = car_data.get('model', 'N/A')
        price = car_data.get('price')
        location = car_data.get('location', 'N/A')
        
        price_text = f"${price:,.0f}" if price else "N/A"
        
        message = f"""
🔔 <b>Триггер сработал!</b>

🎯 <b>Триггер:</b> {trigger_name}
🚗 <b>Автомобиль:</b> {car_id} - {brand} {model}
💰 <b>Цена:</b> {price_text}
📍 <b>Локация:</b> {location}

💬 <b>Сообщение:</b> {formatted_message}
""".strip()
        
        result = await TelegramService.send_message(
            chat_id=settings.farmer_telegram_id,
            text=message
        )
        
        if result:
            logger.info(f"Уведомление о триггере '{trigger_name}' отправлено фермеру")
            return True
        else:
            logger.error(f"Не удалось отправить уведомление о триггере '{trigger_name}'")
            return False

    @staticmethod
    async def send_daily_tasks_summary(db: Session) -> bool:
        """Отправляет ежедневную сводку задач фермеру"""
        if not settings.farmer_telegram_id:
            logger.warning("FARMER_TELEGRAM_ID не установлен")
            return False
        
        from ..services.task_service import TaskService
        from datetime import date, timedelta
        
        # Получаем статистику задач
        today = date.today()
        overdue_tasks = db.query(Task).filter(
            Task.due_date < today,
            Task.is_completed == False
        ).count()
        
        today_tasks = db.query(Task).filter(
            Task.due_date == today,
            Task.is_completed == False
        ).count()
        
        tomorrow_tasks = db.query(Task).filter(
            Task.due_date == today + timedelta(days=1),
            Task.is_completed == False
        ).count()
        
        total_active = db.query(Task).filter(Task.is_completed == False).count()
        
        message = f"""
📊 <b>Ежедневная сводка задач</b>

📅 <b>Сегодня ({today.strftime('%d.%m.%Y')}):</b>
• Просроченные: {overdue_tasks} {'❗' if overdue_tasks > 0 else '✅'}
• На сегодня: {today_tasks}
• На завтра: {tomorrow_tasks}
• Всего активных: {total_active}

{f'⚠️ У вас есть {overdue_tasks} просроченных задач!' if overdue_tasks > 0 else '✅ Просроченных задач нет'}
""".strip()
        
        result = await TelegramService.send_message(
            chat_id=settings.farmer_telegram_id,
            text=message
        )
        
        if result:
            logger.info("Ежедневная сводка задач отправлена фермеру")
            return True
        else:
            logger.error("Не удалось отправить ежедневную сводку задач")
            return False 