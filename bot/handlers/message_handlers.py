from aiogram import Dispatcher, types
from aiogram.filters import Command
from ..services.message_handler import MessageHandler
from ..config import FARMER_TELEGRAM_ID


def setup_handlers(dp: Dispatcher, message_handler: MessageHandler):
    """Настройка обработчиков сообщений"""

    @dp.message(Command("start"))
    async def start_handler(message: types.Message):
        """Обработчик команды /start"""
        await message.answer(
            "Добро пожаловать! Я бот-ассистент для связи с менеджером. "
            "Можете писать свои вопросы, и я передам их нашему специалисту."
        )
        
        # Сохраняем информацию о новом клиенте
        await message_handler.handle_client_message(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username,
            content_type="text",
            content="/start"
        )

    @dp.message()
    async def all_messages_handler(message: types.Message):
        """Обработчик всех сообщений"""
        # Определяем тип контента
        content_type = "text"
        content = ""

        if message.text:
            content_type = "text"
            content = message.text
        elif message.voice:
            content_type = "voice"
            content = f"voice_file_id:{message.voice.file_id}"
        elif message.video_note:
            content_type = "video_note"
            content = f"video_note_file_id:{message.video_note.file_id}"
        elif message.document:
            content_type = "document"
            content = f"document_file_id:{message.document.file_id}, filename:{message.document.file_name}"
        elif message.photo:
            content_type = "photo"
            content = f"photo_file_id:{message.photo[-1].file_id}"
        else:
            content_type = "other"
            content = "Неподдерживаемый тип сообщения"

        # Проверяем, от кого сообщение
        if message.from_user.id == FARMER_TELEGRAM_ID:
            # Сообщение от фермера - запускаем рассылку
            await message_handler.handle_farmer_message(content_type, content)
        else:
            # Сообщение от клиента - сохраняем в базу
            await message_handler.handle_client_message(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                content_type=content_type,
                content=content
            )
            
            # Отправляем подтверждение клиенту
            await message.answer(
                "Спасибо за ваше сообщение! Наш менеджер обязательно с вами свяжется."
            )