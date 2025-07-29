from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard():
    """Главное меню фермера"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Создать рассылку", callback_data="create_broadcast")],
        [InlineKeyboardButton(text="👋 Настроить приветствие", callback_data="greeting_menu")],
        [InlineKeyboardButton(text="📊 Статус приветствия", callback_data="greeting_status")],
        [InlineKeyboardButton(text="🔍 Проверить клиентов", callback_data="validate_clients")],
    ])
    return keyboard


def get_broadcast_menu_keyboard():
    """Меню создания рассылки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ С приветствием", callback_data="broadcast_with_greeting")],
        [InlineKeyboardButton(text="📝 Только сообщение", callback_data="broadcast_without_greeting")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
    ])
    return keyboard


def get_greeting_menu_keyboard():
    """Меню настройки приветствия"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Установить новое", callback_data="set_greeting")],
        [InlineKeyboardButton(text="🗑️ Очистить приветствие", callback_data="clear_greeting")],
        [InlineKeyboardButton(text="👀 Посмотреть текущее", callback_data="show_greeting")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
    ])
    return keyboard


def get_preview_keyboard():
    """Клавиатура для предпросмотра"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_send")],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_content")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_broadcast")],
    ])
    return keyboard


def get_greeting_preview_keyboard():
    """Клавиатура для предпросмотра приветствия"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_greeting")],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_greeting")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_greeting")],
    ])
    return keyboard


def get_cancel_keyboard():
    """Кнопка отмены"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_action")],
    ])
    return keyboard


def get_back_keyboard():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
    ])
    return keyboard 