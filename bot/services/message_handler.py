import asyncio
from typing import List, Dict, Any
from aiogram import Bot
from .api_client import APIClient
from config import FARMER_TELEGRAM_ID


class MessageHandler:
    def __init__(self, bot: Bot, api_client: APIClient):
        self.bot = bot
        self.api_client = api_client

    async def handle_client_message(self, telegram_id: int, first_name: str, last_name: str, 
                                  username: str, content_type: str, content: str):
        """Обработка сообщения от клиента"""
        # Получаем или создаем клиента
        client = await self.api_client.get_or_create_client(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        
        if not client:
            print(f"Не удалось создать/получить клиента {telegram_id}")
            return

        # Сохраняем сообщение
        await self.api_client.create_message(
            client_id=client["id"],
            sender="client",
            content_type=content_type,
            content=content
        )


