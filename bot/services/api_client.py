import httpx
import asyncio
from typing import Optional, Dict, Any
from ..config import BACKEND_URL


class APIClient:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def get_or_create_client(self, telegram_id: int, first_name: str = None, 
                                 last_name: str = None, username: str = None) -> Optional[Dict[Any, Any]]:
        """Получить или создать клиента"""
        try:
            # Сначала пытаемся найти клиента
            response = await self.client.get(f"{self.base_url}/api/v1/clients/telegram/{telegram_id}")
            if response.status_code == 200:
                return response.json()
            
            # Если не найден, создаем нового
            client_data = {
                "telegram_id": telegram_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username
            }
            response = await self.client.post(f"{self.base_url}/api/v1/clients/", json=client_data)
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            print(f"Ошибка при работе с клиентом: {e}")
        
        return None

    async def create_message(self, client_id: int, sender: str, content_type: str, content: str) -> Optional[Dict[Any, Any]]:
        """Создать новое сообщение"""
        try:
            message_data = {
                "client_id": client_id,
                "sender": sender,
                "content_type": content_type,
                "content": content
            }
            response = await self.client.post(f"{self.base_url}/api/v1/messages/", json=message_data)
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Ошибка при создании сообщения: {e}")
        
        return None

    async def get_all_clients(self) -> list:
        """Получить всех клиентов для рассылки"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/clients/")
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Ошибка при получении клиентов: {e}")
        
        return []

    async def send_message_to_client(self, telegram_id: int, message: str) -> bool:
        """Отправляет сообщение клиенту через API (заглушка для будущей интеграции)"""
        # Здесь будет логика отправки сообщения через бота
        # Пока возвращаем True как успешную отправку
        return True