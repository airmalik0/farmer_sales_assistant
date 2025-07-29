from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    """Состояния для создания рассылки"""
    main_menu = State()
    create_broadcast = State()
    waiting_for_content = State()
    preview_broadcast = State()
    
    # Состояния для настройки приветствия
    greeting_menu = State()
    waiting_for_greeting = State()
    preview_greeting = State() 