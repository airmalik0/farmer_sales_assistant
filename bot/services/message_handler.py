import asyncio
from typing import List, Dict, Any
from aiogram import Bot
from .api_client import APIClient
from ..config import FARMER_TELEGRAM_ID


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

    async def handle_farmer_message(self, content_type: str, content: str):
        """Обработка сообщения от фермера для массовой рассылки"""
        # Получаем всех клиентов
        clients = await self.api_client.get_all_clients()
        
        if not clients:
            await self.bot.send_message(
                FARMER_TELEGRAM_ID, 
                "Нет клиентов для рассылки"
            )
            return

        # Отправляем сообщения всем клиентам
        success_count = 0
        for client in clients:
            try:
                # Персонализированное приветствие
                greeting = f"Добрый день, {client['first_name'] or 'дорогой клиент'}, как вы?"
                await self.bot.send_message(client["telegram_id"], greeting)
                
                # Основное сообщение
                if content_type == "text":
                    await self.bot.send_message(client["telegram_id"], content)
                elif content_type == "voice":
                    # Здесь должна быть логика отправки голосового сообщения
                    await self.bot.send_message(client["telegram_id"], "[Голосовое сообщение]")
                elif content_type == "video_note":
                    # Здесь должна быть логика отправки видео-кружка
                    await self.bot.send_message(client["telegram_id"], "[Видео-кружок]")
                elif content_type == "document":
                    # Здесь должна быть логика отправки документа
                    await self.bot.send_message(client["telegram_id"], "[Документ]")
                elif content_type == "photo":
                    # Здесь должна быть логика отправки фото
                    await self.bot.send_message(client["telegram_id"], "[Фото]")
                
                # Сохраняем сообщение в базе
                await self.api_client.create_message(
                    client_id=client["id"],
                    sender="farmer",
                    content_type=content_type,
                    content=content
                )
                
                success_count += 1
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Ошибка при отправке сообщения клиенту {client['telegram_id']}: {e}")

        # Уведомляем фермера о результате
        await self.bot.send_message(
            FARMER_TELEGRAM_ID,
            f"Рассылка завершена. Отправлено {success_count} из {len(clients)} сообщений."
        )

    async def send_message_to_client(self, telegram_id: int, content_type: str, content: str):
        """Отправка сообщения конкретному клиенту (из админ панели)"""
        try:
            if content_type == "text":
                await self.bot.send_message(telegram_id, content)
            # Добавить обработку других типов контента
            return True
        except Exception as e:
            print(f"Ошибка при отправке сообщения клиенту {telegram_id}: {e}")
            return False