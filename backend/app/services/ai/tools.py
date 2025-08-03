"""Инструменты для AI агентов, организованные по модулям"""

from typing import Any, Optional, Literal
from langchain_core.tools import tool


# =============================================================================
# ИНСТРУМЕНТЫ ДЛЯ ДОСЬЕ
# =============================================================================

@tool
def update_dossier_field(field: str, value: Any) -> str:
    """
    Обновить поле в досье клиента.
    
    Args:
        field: Название поля для обновления (phone, current_location, birthday, gender, client_type, personal_notes, business_profile)
        value: Новое значение поля
    """
    allowed_fields = ['phone', 'current_location', 'birthday', 'gender', 'client_type', 'personal_notes', 'business_profile']
    if field not in allowed_fields:
        return f"Ошибка: поле '{field}' не поддерживается. Доступные поля: {', '.join(allowed_fields)}"
    
    return f"Поле '{field}' будет обновлено на значение: {value}"


@tool
def confirm_all_dossier() -> str:
    """Подтвердить все текущие поля досье без изменений."""
    return "Все поля досье подтверждены"


# =============================================================================
# ИНСТРУМЕНТЫ ДЛЯ АВТОМОБИЛЬНЫХ ИНТЕРЕСОВ
# =============================================================================

@tool
def add_car_interest_query(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    mileage_max: Optional[int] = None,
    exterior_color: Optional[str] = None,
    interior_color: Optional[str] = None,
    engine_type: Optional[str] = None,
    drive_type: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """Добавить новый запрос автомобильных интересов."""
    return f"Новый запрос автомобильных интересов добавлен"


@tool
def update_car_interest_query(
    index: int,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    mileage_max: Optional[int] = None,
    exterior_color: Optional[str] = None,
    interior_color: Optional[str] = None,
    engine_type: Optional[str] = None,
    drive_type: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """Обновить существующий запрос автомобильных интересов."""
    return f"Запрос автомобильных интересов #{index} обновлен"


@tool
def delete_car_interest_query(index: int) -> str:
    """Удалить запрос автомобильных интересов."""
    return f"Запрос автомобильных интересов #{index} удален"


@tool
def confirm_all_car_interests() -> str:
    """Подтвердить все текущие автомобильные интересы без изменений."""
    return "Все автомобильные интересы подтверждены"


# =============================================================================
# ИНСТРУМЕНТЫ ДЛЯ ЗАДАЧ
# =============================================================================

@tool
def add_task(description: str, due_date: Optional[str], priority: Literal["low", "normal", "high"]) -> str:
    """Добавить новую задачу."""
    return f"Задача добавлена: {description} (срок: {due_date or 'не указан'}, приоритет: {priority})"


@tool
def update_task(task_id: int, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[Literal["low", "normal", "high"]] = None) -> str:
    """Обновить существующую задачу."""
    updates = []
    if description: updates.append(f"описание: {description}")
    if due_date: updates.append(f"срок: {due_date}")
    if priority: updates.append(f"приоритет: {priority}")
    
    return f"Задача {task_id} обновлена: {', '.join(updates) if updates else 'без изменений'}"


@tool
def complete_task(task_id: int) -> str:
    """Отметить задачу как выполненную."""
    return f"Задача {task_id} отмечена как выполненная"


@tool
def delete_task(task_id: int) -> str:
    """Удалить задачу."""
    return f"Задача {task_id} удалена"


@tool
def confirm_all_tasks() -> str:
    """Подтвердить все текущие задачи без изменений."""
    return "Все задачи подтверждены"


# =============================================================================
# ГРУППИРОВКА ИНСТРУМЕНТОВ ПО ТИПАМ
# =============================================================================

DOSSIER_TOOLS = [
    update_dossier_field,
    confirm_all_dossier
]

CAR_INTEREST_TOOLS = [
    add_car_interest_query,
    update_car_interest_query,
    delete_car_interest_query,
    confirm_all_car_interests
]

TASK_TOOLS = [
    add_task,
    update_task,
    complete_task,
    delete_task,
    confirm_all_tasks
] 