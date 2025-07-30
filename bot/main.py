import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from config import BOT_TOKEN
from services.api_client import APIClient
from services.message_handler import MessageHandler
from handlers import setup_handlers


async def error_handler(event: ErrorEvent):
    """Глобальный обработчик ошибок"""
    logging.error(f"Произошла ошибка: {event.exception}", exc_info=True)
    
    # Если есть возможность отправить сообщение пользователю
    if event.update.message:
        try:
            await event.update.message.answer(
                "❌ <b>Произошла техническая ошибка</b>\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Попробуйте повторить действие\n"
                "• Если ошибка повторяется, используйте /menu\n"
                "• При необходимости обратитесь к администратору"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение об ошибке: {e}")
    
    return True


async def main():
    """Главная функция запуска бота"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Проверяем наличие токена
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN не установлен!")
        return

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем глобальный обработчик ошибок
    dp.errors.register(error_handler)
    
    # Инициализация сервисов
    api_client = APIClient()
    message_handler = MessageHandler(bot, api_client)
    
    # Настройка обработчиков
    setup_handlers(dp, message_handler)
    
    try:
        logging.info("Бот запущен...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await api_client.close()


if __name__ == "__main__":
    asyncio.run(main())