import httpx
import logging
from typing import Dict
from ..core.config import settings

logger = logging.getLogger(__name__)


class TelegramAdminService:
    API_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    FARMER_ID = settings.farmer_telegram_id
    
    @staticmethod
    async def send_notification(message: str):
        """Отправка уведомления админу"""
        url = f"{TelegramAdminService.API_URL}/sendMessage"
        payload = {
            "chat_id": TelegramAdminService.FARMER_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return True
            except httpx.RequestError as e:
                logger.error(f"Ошибка отправки уведомления админу: {e}")
                return False
    
    @staticmethod
    async def send_fallback_message(telegram_id: int, text: str):
        """Fallback отправка через Telegram Bot API"""
        url = f"{TelegramAdminService.API_URL}/sendMessage"
        payload = {
            "chat_id": telegram_id,
            "text": f"📱 [Fallback] {text}",
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                # Уведомляем админа об использовании fallback
                await TelegramAdminService.send_notification(
                    f"⚠️ Использован fallback для отправки сообщения пользователю {telegram_id}"
                )
                
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Fallback отправка не удалась: {e}")
                return None
    
    @staticmethod
    async def send_broadcast_summary(sent_count: int, failed_count: int, channels: Dict[str, int]):
        """Отправка результатов рассылки"""
        message = f"""
📢 <b>Результаты рассылки</b>

✅ Отправлено: {sent_count}
❌ Ошибки: {failed_count}

📊 <b>По каналам:</b>
"""
        for channel, count in channels.items():
            channel_name = "WhatsApp" if channel == "whatsapp" else "Telegram"
            message += f"• {channel_name}: {count}\n"
            
        await TelegramAdminService.send_notification(message)
    
    @staticmethod
    async def send_new_client_notification(client):
        """Уведомление о новом клиенте"""
        channel_name = "WhatsApp" if client.provider == "whatsapp" else "Telegram"
        message = f"""
👤 <b>Новый клиент</b>

📱 Канал: {channel_name}
👤 Имя: {client.name or 'Не указано'}
📞 Контакт: {client.phone_number or client.username or client.sender_external_id}
🕐 Время: {client.created_at.strftime('%d.%m.%Y %H:%M')}
"""
        await TelegramAdminService.send_notification(message) 