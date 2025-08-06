import httpx
import asyncio
import logging
from typing import Optional, Dict, List, Any
from ..core.config import settings

logger = logging.getLogger(__name__)

class PactService:
    """Сервис для работы с Pact API V2"""
    
    BASE_URL = "https://api.pact.im"  # Base Pact API URL
    API_TOKEN = settings.pact_api_token
    COMPANY_ID = settings.pact_company_id
    
    # Rate limiting: 5 запросов в секунду, 30 в минуту
    _send_semaphore = asyncio.Semaphore(5)
    _last_send_times = []
    
    @classmethod
    async def _wait_for_rate_limit(cls):
        """Соблюдение rate limiting: max 5 req/sec, 30 req/min"""
        async with cls._send_semaphore:
            now = asyncio.get_event_loop().time()
            
            # Очищаем старые записи (старше 60 секунд)
            cls._last_send_times = [t for t in cls._last_send_times if now - t < 60]
            
            # Проверяем лимит за минуту
            if len(cls._last_send_times) >= 30:
                sleep_time = 60 - (now - cls._last_send_times[0])
                if sleep_time > 0:
                    logger.info(f"Rate limit: ждем {sleep_time:.2f}с")
                    await asyncio.sleep(sleep_time)
            
            # Проверяем лимит за секунду
            recent_requests = [t for t in cls._last_send_times if now - t < 1]
            if len(recent_requests) >= 5:
                await asyncio.sleep(0.2)  # 200ms между запросами
            
            cls._last_send_times.append(now)
    
    @staticmethod
    async def send_message_to_conversation(
        conversation_id: int, 
        text: str = None, 
        attachment_ids: List[int] = None,
        replied_to_id: str = None,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """Отправка сообщения в conversation через Pact API"""
        
        await PactService._wait_for_rate_limit()
        
        url = f"{PactService.BASE_URL}/v1/companies/messages"
        headers = {
            "X-Private-Api-Token": PactService.API_TOKEN,
            "Content-Type": "application/json"
        }
        
        payload = {
            "conversation_id": conversation_id
        }
        
        if text:
            payload["message"] = text
        
        if attachment_ids:
            payload["attachment_ids"] = attachment_ids
            
        if replied_to_id:
            payload["replied_to_id"] = replied_to_id
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        logger.info(f"Сообщение отправлено в conversation {conversation_id}")
                        return response.json()
                    else:
                        logger.error(f"Ошибка отправки сообщения: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения (попытка {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    @staticmethod
    async def send_first_message_with_fallback(
        provider: str,
        contact: str, 
        text: str,
        attachment_ids: List[int] = None
    ) -> Optional[Dict]:
        """Отправка первого сообщения с fallback на Telegram Bot API"""
        
        await PactService._wait_for_rate_limit()
        
        url = f"{PactService.BASE_URL}/v1/companies/channels/messages"
        headers = {
            "X-Private-Api-Token": PactService.API_TOKEN,
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel_type": provider,
            "external_id": contact,
            "message": text
        }
        
        if attachment_ids:
            payload["attachment_ids"] = attachment_ids
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"Первое сообщение отправлено через {provider} на {contact}")
                    return response.json()
                else:
                    logger.error(f"Ошибка отправки первого сообщения: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка отправки первого сообщения через Pact: {e}")
        
        # Fallback для telegram_personal
        if provider == "telegram_personal":
            try:
                from .telegram_admin_service import TelegramAdminService
                success = await TelegramAdminService.send_fallback_message(int(contact), text)
                if success:
                    logger.info(f"Fallback сообщение отправлено через Telegram Bot API")
                    return {"fallback": True, "success": True}
            except Exception as e:
                logger.error(f"Ошибка fallback отправки: {e}")
        
        return None
    
    @staticmethod 
    async def get_conversations(page: int = 1, per_page: int = 25) -> Optional[Dict]:
        """Получение списка бесед через Pact API"""
        
        await PactService._wait_for_rate_limit()
        
        # Используем правильный V1 API endpoint с company_id
        url = f"{PactService.BASE_URL}/p1/companies/{PactService.COMPANY_ID}/conversations"
        headers = {
            "X-Private-Api-Token": PactService.API_TOKEN
        }
        params = {
            "page": page,
            "per": per_page,
            "sort_direction": "desc"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Ошибка получения бесед: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения бесед: {e}")
        
        return None
    
    @staticmethod
    async def upload_attachment(
        file_content: bytes,
        filename: str,
        mime_type: str,
        metadata: Dict = None
    ) -> Optional[Dict]:
        """Загрузка вложения в Pact"""
        
        await PactService._wait_for_rate_limit()
        
        url = f"{PactService.BASE_URL}/v1/companies/attachments"
        headers = {
            "X-Private-Api-Token": PactService.API_TOKEN
        }
        
        files = {
            "file": (filename, file_content, mime_type)
        }
        
        data = {}
        if metadata:
            data.update(metadata)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    logger.info(f"Вложение {filename} загружено")
                    return response.json()
                else:
                    logger.error(f"Ошибка загрузки вложения: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки вложения: {e}")
        
        return None
    
    @staticmethod
    async def get_conversation_messages(
        conversation_id: int,
        page: int = 1, 
        per_page: int = 150
    ) -> Optional[Dict]:
        """Получение сообщений беседы через Pact API"""
        
        await PactService._wait_for_rate_limit()
        
        # Используем правильный V1 API endpoint
        url = f"{PactService.BASE_URL}/p1/companies/{PactService.COMPANY_ID}/conversations/{conversation_id}/messages"
        headers = {
            "X-Private-Api-Token": PactService.API_TOKEN
        }
        
        params = {
            "page": page,
            "per": per_page,
            "sort_direction": "desc"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Ошибка получения сообщений: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения сообщений: {e}")
        
        return None 