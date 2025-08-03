from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import httpx
import os

admin_router = Router()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FARMER_ID = int(os.getenv("FARMER_TELEGRAM_ID"))

def setup_admin_handlers(dp):
    dp.include_router(admin_router)

@admin_router.message(Command("start"))
async def cmd_start(message: Message):
    """Приветствие только для админа"""
    if message.from_user.id != FARMER_ID:
        await message.answer("❌ Это админ-бот. Клиентские сообщения обрабатываются через Pact API.")
        return
    
    await message.answer("""
🎛 <b>Админ-панель Farmer Sales Assistant</b>
<i>Все клиентские сообщения через Pact API</i>

📊 /stats - Статистика по каналам
👥 /clients - Список клиентов  
📢 /broadcast - Запуск рассылки
🔧 /settings - Настройки Pact
🔄 /sync - Синхронизация с Pact
""")

@admin_router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика по каналам Pact"""
    if message.from_user.id != FARMER_ID:
        return
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BACKEND_URL}/api/v1/admin/stats")
            data = response.json()
            
            stats_text = f"""
📊 <b>Статистика Pact каналов</b>

👥 <b>Клиенты:</b>
• WhatsApp: {data['clients']['whatsapp']}
• Telegram Personal: {data['clients']['telegram_personal']}
• Всего: {data['clients']['total']}

💬 <b>Сообщения (сегодня):</b>
• Входящие: {data['messages']['incoming']}
• Исходящие: {data['messages']['outgoing']}

✅ <b>Для рассылки:</b> {data['clients']['approved']}

🔗 <b>Pact статус:</b>
• API подключение: {data['pact']['status']}
• Последний webhook: {data['pact']['last_webhook']}
"""
            await message.answer(stats_text)
            
        except Exception as e:
            await message.answer(f"❌ Ошибка получения статистики: {e}")

@admin_router.message(Command("sync"))
async def cmd_sync(message: Message):
    """Синхронизация с Pact API"""
    if message.from_user.id != FARMER_ID:
        return
    
    await message.answer("🔄 Запуск синхронизации с Pact...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BACKEND_URL}/api/v1/admin/sync-conversations")
            data = response.json()
            
            await message.answer(f"""
✅ <b>Синхронизация завершена</b>

📥 Найдено бесед: {data['total_conversations']}
👤 Создано клиентов: {data['created_clients']}
""")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка синхронизации: {e}")

@admin_router.message(Command("clients"))
async def cmd_clients(message: Message):
    """Список клиентов"""
    if message.from_user.id != FARMER_ID:
        return
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BACKEND_URL}/api/v1/clients")
            clients = response.json()
            
            if not clients:
                await message.answer("👥 Клиентов пока нет")
                return
            
            clients_text = "👥 <b>Список клиентов:</b>\n\n"
            for client in clients[:10]:  # Показываем первых 10
                channel = "📱 WhatsApp" if client['provider'] == 'whatsapp' else "💬 Telegram"
                clients_text += f"{channel} <b>{client['name'] or 'Без имени'}</b>\n"
                clients_text += f"ID: {client['id']} | Создан: {client['created_at'][:10]}\n\n"
            
            if len(clients) > 10:
                clients_text += f"... и еще {len(clients) - 10} клиентов"
            
            await message.answer(clients_text)
            
        except Exception as e:
            await message.answer(f"❌ Ошибка получения клиентов: {e}")

@admin_router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Настройки Pact"""
    if message.from_user.id != FARMER_ID:
        return
    
    await message.answer("""
🔧 <b>Настройки Pact API</b>

Доступные команды:
• /webhook_status - Статус webhook
• /channels - Статус каналов
• /test_api - Тест API подключения

ℹ️ Для изменения настроек используйте веб-интерфейс
""")

# Обработчик всех остальных сообщений (отклоняем клиентские)
@admin_router.message()
async def handle_other_messages(message: Message):
    """Обработчик всех остальных сообщений"""
    if message.from_user.id != FARMER_ID:
        await message.answer("❌ Это админ-бот. Клиентские сообщения обрабатываются через Pact API.")
        return
    
    await message.answer("🤖 Используйте /start для просмотра доступных команд") 