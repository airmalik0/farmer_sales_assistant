from aiogram import Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from services.message_handler import MessageHandler
from config import FARMER_TELEGRAM_ID
from states.broadcast_states import BroadcastStates
from handlers.menu_handlers import MenuHandlers


def setup_handlers(dp: Dispatcher, message_handler: MessageHandler):
    """Настройка обработчиков сообщений"""
    
    # Инициализируем обработчики меню
    menu_handlers = MenuHandlers(message_handler)

    @dp.message(Command("start"))
    async def start_handler(message: types.Message, state: FSMContext):
        """Обработчик команды /start"""
        if message.from_user.id == FARMER_TELEGRAM_ID:
            # Фермер запускает бота - показываем меню
            await menu_handlers.cmd_menu(message, state)
        else:
            # Клиент запускает бота - сохраняем информацию
            await message_handler.handle_client_message(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                content_type="text",
                content="/start"
            )

    @dp.message(Command("menu"))
    async def menu_command(message: types.Message, state: FSMContext):
        """Команда /menu - показывает главное меню"""
        await menu_handlers.cmd_menu(message, state)

    # Обработчики callback'ов
    @dp.callback_query(StateFilter(BroadcastStates.main_menu))
    async def main_menu_callbacks(callback: types.CallbackQuery, state: FSMContext):
        await menu_handlers.main_menu_callback(callback, state)

    @dp.callback_query(StateFilter(BroadcastStates.create_broadcast))
    async def broadcast_menu_callbacks(callback: types.CallbackQuery, state: FSMContext):
        await menu_handlers.broadcast_menu_callback(callback, state)

    @dp.callback_query(StateFilter(BroadcastStates.greeting_menu))
    async def greeting_menu_callbacks(callback: types.CallbackQuery, state: FSMContext):
        await menu_handlers.greeting_menu_callback(callback, state)

    @dp.callback_query(StateFilter(BroadcastStates.preview_broadcast, BroadcastStates.preview_greeting))
    async def preview_callbacks(callback: types.CallbackQuery, state: FSMContext):
        await menu_handlers.preview_callbacks(callback, state)

    # Добавляем обработчики для состояний ожидания ввода
    @dp.callback_query(StateFilter(BroadcastStates.waiting_for_content))
    async def waiting_content_callbacks(callback: types.CallbackQuery, state: FSMContext):
        if callback.data == "cancel_action":
            await menu_handlers.cancel_action(callback, state)
        elif callback.data == "back_to_main":
            await menu_handlers.back_to_main_action(callback, state)

    @dp.callback_query(StateFilter(BroadcastStates.waiting_for_greeting))
    async def waiting_greeting_callbacks(callback: types.CallbackQuery, state: FSMContext):
        if callback.data == "cancel_action":
            await menu_handlers.cancel_action(callback, state)
        elif callback.data == "back_to_main":
            await menu_handlers.back_to_main_action(callback, state)

    @dp.callback_query(F.data == "cancel_action")
    async def cancel_callbacks(callback: types.CallbackQuery, state: FSMContext):
        await menu_handlers.cancel_action(callback, state)

    @dp.callback_query(F.data == "back_to_main")
    async def back_callbacks(callback: types.CallbackQuery, state: FSMContext):
        await menu_handlers.back_to_main_action(callback, state)

    # Обработчики сообщений в состояниях
    @dp.message(StateFilter(BroadcastStates.waiting_for_content))
    async def broadcast_content_handler(message: types.Message, state: FSMContext):
        await menu_handlers.handle_broadcast_content(message, state)

    @dp.message(StateFilter(BroadcastStates.waiting_for_greeting))
    async def greeting_content_handler(message: types.Message, state: FSMContext):
        await menu_handlers.handle_greeting_content(message, state)

    # Обработчик сообщений от клиентов (не в состоянии FSM)
    @dp.message(StateFilter(None))
    async def client_messages_handler(message: types.Message):
        """Обработчик сообщений от клиентов"""
        if message.from_user.id == FARMER_TELEGRAM_ID:
            # Если фермер пишет без состояния, показываем меню
            await message.reply(
                "🤖 Используйте /menu для доступа к панели управления рассылками"
            )
            return

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

        # Сообщение от клиента - сохраняем в базу
        await message_handler.handle_client_message(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username,
            content_type=content_type,
            content=content
        )