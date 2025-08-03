import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers.admin_handlers import setup_admin_handlers

async def main():
    """Главная функция запуска ТОЛЬКО админ-бота"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Проверяем наличие токена
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    
    # ТОЛЬКО админ-хендлеры (никаких клиентских обработчиков)
    setup_admin_handlers(dp)
    
    logging.info("Запуск админ-бота (без клиентских функций)...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())