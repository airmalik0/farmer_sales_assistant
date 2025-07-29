from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from services.message_handler import MessageHandler
from config import FARMER_TELEGRAM_ID
from states.broadcast_states import BroadcastStates
from keyboards.inline_keyboards import (
    get_main_menu_keyboard,
    get_broadcast_menu_keyboard,
    get_greeting_menu_keyboard,
    get_preview_keyboard,
    get_greeting_preview_keyboard,
    get_cancel_keyboard,
    get_back_keyboard
)


class MenuHandlers:
    def __init__(self, message_handler: MessageHandler):
        self.message_handler = message_handler

    async def cmd_menu(self, message: types.Message, state: FSMContext):
        """Команда /menu - показывает главное меню"""
        if message.from_user.id != FARMER_TELEGRAM_ID:
            return
        
        await state.set_state(BroadcastStates.main_menu)
        await message.answer(
            "🌾 <b>Меню управления рассылками</b>\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )

    async def main_menu_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Обработчик главного меню"""
        if callback.from_user.id != FARMER_TELEGRAM_ID:
            await callback.answer("У вас нет доступа к этому меню")
            return

        await callback.answer()

        if callback.data == "create_broadcast":
            await state.set_state(BroadcastStates.create_broadcast)
            await callback.message.edit_text(
                "📢 <b>Создание рассылки</b>\n\n"
                "Выберите тип рассылки:",
                reply_markup=get_broadcast_menu_keyboard()
            )

        elif callback.data == "greeting_menu":
            await state.set_state(BroadcastStates.greeting_menu)
            await callback.message.edit_text(
                "👋 <b>Настройка приветствия</b>\n\n"
                "Выберите действие:",
                reply_markup=get_greeting_menu_keyboard()
            )

        elif callback.data == "greeting_status":
            try:
                greeting_data = await self.message_handler.api_client.get_greeting()
                if greeting_data:
                    if greeting_data.get("is_custom", False):
                        text = f"📝 <b>Текущее приветствие:</b>\n\n{greeting_data['greeting_text']}\n\n<i>Переменные [Имя Клиента] и [Фамилия Клиента] будут заменены на реальные имена</i>"
                    else:
                        text = f"📝 <b>Стандартное приветствие:</b>\n\n{greeting_data['greeting_text']}\n\n<i>Кастомное приветствие не установлено</i>"
                else:
                    text = "❌ Ошибка при получении приветствия"
            except Exception as e:
                text = f"❌ Ошибка: {str(e)}"
            
            await callback.message.edit_text(text, reply_markup=get_back_keyboard())

        elif callback.data == "validate_clients":
            # Проверяем клиентов через API
            try:
                result = await self.message_handler.api_client.validate_broadcast_clients()
                if result:
                    text = f"🔍 <b>Статус клиентов:</b>\n\n"
                    text += f"👥 Всего клиентов: {result['total_clients']}\n"
                    text += f"✅ Готовы к рассылке: {result['clients_ready']}\n"
                    
                    if result['clients_without_names']:
                        text += f"❌ Без имени: {len(result['clients_without_names'])}\n"
                    
                    if result['clients_with_unapproved_names']:
                        text += f"⏳ Имена не одобрены: {len(result['clients_with_unapproved_names'])}\n"
                    
                    if result['can_broadcast']:
                        text += "\n✅ <b>Рассылка возможна!</b>"
                    else:
                        text += "\n❌ <b>Рассылка невозможна</b>\nНеобходимо одобрить всех клиентов"
                else:
                    text = "❌ Ошибка при проверке клиентов"
            except Exception as e:
                text = f"❌ Ошибка: {str(e)}"
            
            await callback.message.edit_text(text, reply_markup=get_back_keyboard())

        elif callback.data == "back_to_main":
            # Возврат в главное меню (на случай если уже в главном меню)
            await self.show_main_menu(callback.message, state)

    async def broadcast_menu_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Обработчик меню создания рассылки"""
        await callback.answer()

        if callback.data == "broadcast_with_greeting":
            await state.update_data(include_greeting=True)
            await state.set_state(BroadcastStates.waiting_for_content)
            await callback.message.edit_text(
                "✏️ <b>Отправьте содержимое рассылки</b>\n\n"
                "Вы можете отправить:\n"
                "• Текстовое сообщение\n"
                "• Голосовое сообщение\n"
                "• Фото\n"
                "• Видео-кружок\n"
                "• Документ\n\n"
                "<i>Рассылка будет отправлена С приветствием</i>",
                reply_markup=get_cancel_keyboard()
            )

        elif callback.data == "broadcast_without_greeting":
            await state.update_data(include_greeting=False)
            await state.set_state(BroadcastStates.waiting_for_content)
            await callback.message.edit_text(
                "✏️ <b>Отправьте содержимое рассылки</b>\n\n"
                "Вы можете отправить:\n"
                "• Текстовое сообщение\n"
                "• Голосовое сообщение\n"
                "• Фото\n"
                "• Видео-кружок\n"
                "• Документ\n\n"
                "<i>Рассылка будет отправлена БЕЗ приветствия</i>",
                reply_markup=get_cancel_keyboard()
            )

        elif callback.data == "back_to_main":
            await self.show_main_menu(callback.message, state)

    async def greeting_menu_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Обработчик меню приветствия"""
        await callback.answer()

        if callback.data == "set_greeting":
            await state.set_state(BroadcastStates.waiting_for_greeting)
            await callback.message.edit_text(
                "✏️ <b>Введите новое приветствие</b>\n\n"
                "Вы можете использовать переменные:\n"
                "• <code>[Имя Клиента]</code> - имя клиента\n"
                "• <code>[Фамилия Клиента]</code> - фамилия клиента\n\n"
                "Пример: <i>Привет, [Имя Клиента]! Как дела?</i>",
                reply_markup=get_cancel_keyboard()
            )

        elif callback.data == "clear_greeting":
            try:
                result = await self.message_handler.api_client.clear_greeting()
                if result:
                    text = "🗑️ <b>Приветствие очищено</b>\n\nТеперь будет использоваться стандартное приветствие"
                else:
                    text = "❌ Ошибка при очистке приветствия"
            except Exception as e:
                text = f"❌ Ошибка: {str(e)}"
            
            await callback.message.edit_text(text, reply_markup=get_back_keyboard())

        elif callback.data == "show_greeting":
            try:
                greeting_data = await self.message_handler.api_client.get_greeting()
                if greeting_data:
                    if greeting_data.get("is_custom", False):
                        text = f"📝 <b>Кастомное приветствие:</b>\n\n{greeting_data['greeting_text']}"
                    else:
                        text = f"📝 <b>Стандартное приветствие:</b>\n\n{greeting_data['greeting_text']}"
                else:
                    text = "❌ Ошибка при получении приветствия"
            except Exception as e:
                text = f"❌ Ошибка: {str(e)}"
            
            await callback.message.edit_text(text, reply_markup=get_back_keyboard())

        elif callback.data == "back_to_main":
            await self.show_main_menu(callback.message, state)



    async def handle_broadcast_content(self, message: types.Message, state: FSMContext):
        """Обработка содержимого рассылки"""
        if message.from_user.id != FARMER_TELEGRAM_ID:
            return

        # Определяем тип контента
        content_type, content = self._extract_content(message)
        
        # Сохраняем данные
        await state.update_data(
            content_type=content_type,
            content=content
        )
        
        # Показываем предпросмотр
        data = await state.get_data()
        include_greeting = data.get("include_greeting", False)
        
        preview_text = "📋 <b>Предпросмотр рассылки</b>\n\n"
        
        if include_greeting:
            try:
                greeting_data = await self.message_handler.api_client.get_greeting()
                greeting_text = greeting_data.get("greeting_text", "Добрый день, [Имя Клиента], как вы?") if greeting_data else "Добрый день, [Имя Клиента], как вы?"
            except:
                greeting_text = "Добрый день, [Имя Клиента], как вы?"
            
            preview_text += f"👋 <b>Приветствие:</b>\n{greeting_text}\n\n"
        
        preview_text += f"📝 <b>Содержимое:</b>\n"
        
        if content_type == "text":
            preview_text += content
        else:
            preview_text += f"<i>{self._get_content_description(content_type)}</i>"
        
        await state.set_state(BroadcastStates.preview_broadcast)
        await message.answer(preview_text, reply_markup=get_preview_keyboard())

    async def handle_greeting_content(self, message: types.Message, state: FSMContext):
        """Обработка содержимого приветствия"""
        if message.from_user.id != FARMER_TELEGRAM_ID:
            return

        if not message.text:
            await message.answer("❌ Приветствие должно быть текстом")
            return

        greeting = message.text.strip()
        await state.update_data(greeting=greeting)
        
        preview_text = f"📋 <b>Предпросмотр приветствия</b>\n\n"
        preview_text += f"📝 <b>Текст:</b>\n{greeting}\n\n"
        preview_text += "<i>Переменные [Имя Клиента] и [Фамилия Клиента] будут заменены на реальные имена</i>"
        
        await state.set_state(BroadcastStates.preview_greeting)
        await message.answer(preview_text, reply_markup=get_greeting_preview_keyboard())

    async def preview_callbacks(self, callback: types.CallbackQuery, state: FSMContext):
        """Обработчики предпросмотра"""
        await callback.answer()

        if callback.data == "confirm_send":
            # Отправляем рассылку
            data = await state.get_data()
            try:
                result = await self.message_handler.api_client.farmer_broadcast(
                    content_type=data["content_type"],
                    content=data["content"],
                    include_greeting=data.get("include_greeting", False)
                )
                
                if result and result.get("success", True):
                    text = f"✅ <b>Рассылка отправлена!</b>\n\n{result.get('message', 'Рассылка завершена успешно')}"
                else:
                    text = f"❌ <b>Ошибка рассылки</b>\n\n{result.get('message', 'Неизвестная ошибка')}"
                    
            except Exception as e:
                text = f"❌ <b>Ошибка:</b> {str(e)}"
            
            await callback.message.edit_text(text, reply_markup=get_back_keyboard())
            await state.clear()

        elif callback.data == "edit_content":
            await state.set_state(BroadcastStates.waiting_for_content)
            data = await state.get_data()
            include_greeting = data.get("include_greeting", False)
            greeting_text = "С приветствием" if include_greeting else "БЕЗ приветствия"
            
            await callback.message.edit_text(
                f"✏️ <b>Введите новое содержимое</b>\n\n<i>Рассылка будет {greeting_text}</i>",
                reply_markup=get_cancel_keyboard()
            )

        elif callback.data == "cancel_broadcast":
            await self.show_main_menu(callback.message, state)

        elif callback.data == "save_greeting":
            # Сохраняем приветствие
            data = await state.get_data()
            try:
                result = await self.message_handler.api_client.set_greeting(data["greeting"], enabled=True)
                if result:
                    text = f"✅ <b>Приветствие сохранено!</b>\n\nНовое приветствие: {data['greeting']}"
                else:
                    text = "❌ Ошибка при сохранении приветствия"
            except Exception as e:
                text = f"❌ Ошибка: {str(e)}"
            
            await callback.message.edit_text(text, reply_markup=get_back_keyboard())
            await state.clear()

        elif callback.data == "edit_greeting":
            await state.set_state(BroadcastStates.waiting_for_greeting)
            await callback.message.edit_text(
                "✏️ <b>Введите новое приветствие</b>",
                reply_markup=get_cancel_keyboard()
            )

        elif callback.data == "cancel_greeting":
            await self.show_main_menu(callback.message, state)

    async def cancel_action(self, callback: types.CallbackQuery, state: FSMContext):
        """Отмена действия"""
        await callback.answer()
        await self.show_main_menu(callback.message, state)
    
    async def back_to_main_action(self, callback: types.CallbackQuery, state: FSMContext):
        """Возврат к главному меню"""
        await callback.answer()
        await self.show_main_menu(callback.message, state)

    async def show_main_menu(self, message, state: FSMContext):
        """Показать главное меню"""
        await state.set_state(BroadcastStates.main_menu)
        if hasattr(message, 'edit_text'):
            await message.edit_text(
                "🌾 <b>Меню управления рассылками</b>\n\n"
                "Выберите действие:",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer(
                "🌾 <b>Меню управления рассылками</b>\n\n"
                "Выберите действие:",
                reply_markup=get_main_menu_keyboard()
            )

    def _extract_content(self, message: types.Message):
        """Извлекает контент из сообщения"""
        if message.text:
            return "text", message.text
        elif message.voice:
            return "voice", f"voice_file_id:{message.voice.file_id}"
        elif message.video_note:
            return "video_note", f"video_note_file_id:{message.video_note.file_id}"
        elif message.document:
            return "document", f"document_file_id:{message.document.file_id}, filename:{message.document.file_name}"
        elif message.photo:
            return "photo", f"photo_file_id:{message.photo[-1].file_id}"
        else:
            return "other", "Неподдерживаемый тип сообщения"

    def _get_content_description(self, content_type: str):
        """Возвращает описание типа контента"""
        descriptions = {
            "voice": "Голосовое сообщение",
            "video_note": "Видео-кружок",
            "document": "Документ",
            "photo": "Фотография",
            "other": "Другой тип файла"
        }
        return descriptions.get(content_type, "Неизвестный тип") 