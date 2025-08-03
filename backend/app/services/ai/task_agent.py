"""Агент для анализа задач клиента"""

import logging
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Optional

from ...core.database import SessionLocal
from ...models.task import Task
from ...models.message import Message
from .base_agent import BaseAnalysisAgent
from .tools import TASK_TOOLS

logger = logging.getLogger(__name__)


class TaskAnalysisState(TypedDict):
    """Состояние для анализа задач"""
    client_id: int
    client_name: str
    messages: List
    current_tasks: List[Dict[str, Any]]
    manual_modifications: Optional[Dict[str, Any]]
    new_tasks: List[Dict[str, Any]]
    updated_tasks: List[Dict[str, Any]]
    completed_task_ids: List[int]
    deleted_task_ids: List[int]
    confirmed: bool
    errors: List[str]


class TaskAnalysisAgent(BaseAnalysisAgent):
    """Агент для анализа задач"""
    
    def __init__(self):
        super().__init__(TASK_TOOLS, TaskAnalysisState)
    
    def _prepare_context(self, state: TaskAnalysisState) -> TaskAnalysisState:
        """Подготовка контекста для анализа"""
        logger.info(f"Подготовка контекста задач для клиента {state['client_id']}")
        
        # Получаем текущие задачи из БД
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(
                Task.client_id == state['client_id'],
                Task.is_completed == False
            ).all()
            
            state["current_tasks"] = [
                {
                    "id": task.id,
                    "description": task.description,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat()
                }
                for task in tasks
            ]
            
            # Собираем manual_modifications из всех задач клиента
            all_tasks = db.query(Task).filter(Task.client_id == state['client_id']).all()
            state["manual_modifications"] = {}
            for task in all_tasks:
                if task.extra_data and "manual_modifications" in task.extra_data:
                    for field, info in task.extra_data["manual_modifications"].items():
                        state["manual_modifications"][f"task_{task.id}_{field}"] = info
        finally:
            db.close()
        
        state["new_tasks"] = []
        state["updated_tasks"] = []
        state["completed_task_ids"] = []
        state["deleted_task_ids"] = []
        state["confirmed"] = False
        state["errors"] = []
        
        return state
    
    def _generate_system_prompt(self, state: TaskAnalysisState) -> str:
        """Генерирует системный промпт для анализа задач"""
        return self._generate_task_prompt(
            state["client_name"],
            state["current_tasks"],
            state["manual_modifications"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _process_updates(self, state: TaskAnalysisState) -> TaskAnalysisState:
        """Обработка обновлений из вызовов инструментов"""
        # Проверяем tool_calls для извлечения информации
        for message in reversed(state["messages"]):
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call["name"] == "add_task":
                        state["new_tasks"].append({
                            "description": tool_call["args"]["description"],
                            "due_date": tool_call["args"]["due_date"],
                            "priority": tool_call["args"]["priority"]
                        })
                    
                    elif tool_call["name"] == "update_task":
                        update_data = {"task_id": tool_call["args"]["task_id"]}
                        if "description" in tool_call["args"]:
                            update_data["description"] = tool_call["args"]["description"]
                        if "due_date" in tool_call["args"]:
                            update_data["due_date"] = tool_call["args"]["due_date"]
                        if "priority" in tool_call["args"]:
                            update_data["priority"] = tool_call["args"]["priority"]
                        state["updated_tasks"].append(update_data)
                    
                    elif tool_call["name"] == "complete_task":
                        state["completed_task_ids"].append(tool_call["args"]["task_id"])
                    
                    elif tool_call["name"] == "delete_task":
                        state["deleted_task_ids"].append(tool_call["args"]["task_id"])
                    
                    elif tool_call["name"] == "confirm_all_tasks":
                        state["confirmed"] = True
        
        return state
    
    def _generate_task_prompt(self, client_name: str, current_tasks: List[Dict],
                             manual_modifications: Dict, current_time: str) -> str:
        """Создает промпт для анализа и управления задачами по клиенту."""

        # Форматирование текущих задач для наглядности
        tasks_info = ""
        if current_tasks:
            tasks_info = "**Текущие активные задачи:**\n"
            for task in current_tasks:
                due_info = f", срок: {task['due_date']}" if task.get('due_date') else ""
                tasks_info += f"- ID {task['id']}: {task['description']}{due_info}\n"
        else:
            tasks_info = "**Текущие активные задачи:** нет\n"

        # Форматирование информации о ручных изменениях
        manual_info = ""
        if manual_modifications:
            manual_fields = []
            for field_path, info in manual_modifications.items():
                if field_path.startswith("task_"):
                    parts = field_path.split("_", 2)
                    if len(parts) >= 3:
                        task_id, field = parts[1], parts[2]
                        modified_at = info.get('modified_at', 'неизвестно')
                        manual_fields.append(f"- Задача {task_id}, поле '{field}': изменено вручную {modified_at}")
            if manual_fields:
                manual_info = f"""
⚠️ **ЗАДАЧИ, ИЗМЕНЕННЫЕ ВРУЧНУЮ:**
{chr(10).join(manual_fields)}
Обновляй их, только если из переписки явно следует изменение этих параметров."""

        return f"""Ты — проактивный ИИ-ассистент менеджера по продажам.
Твоя задача — анализировать переписку с клиентом {client_name} и фиксировать в виде задач все факты и финальные договоренности.

### ТВОЯ ГЛАВНАЯ ЦЕЛЬ
Превращать диалог в **четкий план действий** для менеджера, гарантируя, что ни одно обязательство или важная дата не будут упущены.

---

### КЛЮЧЕВОЕ ТРЕБОВАНИЕ: ФОРМАТ ОПИСАНИЯ ЗАДАЧИ (`description`)

Каждая задача, которую ты создаешь, должна быть сформулирована как **конкретное, глагольное действие** для менеджера. Задача должна четко отвечать на вопрос «Что нужно сделать?».

- **НЕПРАВИЛЬНО:** "У клиента ДР 15 января."
- **ПРАВИЛЬНО:** "**Поздравить** клиента с ДР 15 января."

- **НЕПРАВИЛЬНО:** "Созвон в 3."
- **ПРАВИЛЬНО:** "**Созвониться** с клиентом для обсуждения подборки."

- **НЕПРАВИЛЬНО:** "Клиент вернулся из отпуска."
- **ПРАВИЛЬНО:** "**Связаться** с клиентом, т.к. он вернулся из отпуска."

---

### ГЛАВНЫЙ ПРИНЦИП: ФИКСИРУЙ ТОЛЬКО СВЕРШИВШИЕСЯ ФАКТЫ

Ты должен четко различать простое обсуждение и итоговую договоренность.

**1. Факты и Односторонние События (Создавать СРАЗУ):**
Если в переписке появляется конкретный факт, ты сразу создаешь **задачу-действие**.
- **Пример:** Клиент пишет "у меня день рождения 15 января" → Твоё действие: `add_task("**Поздравить** клиента с ДР", due_date="2026-01-15 10:00:00", priority="low")`
- **Пример:** Клиент "вернусь после 10-го августа" → Твоё действие: `add_task("**Связаться** с клиентом после отпуска", due_date="2025-08-11 10:00:00", priority="normal")`

**2. Двусторонние Договоренности (Создавать ПОСЛЕ ПОДТВЕРЖДЕНИЯ):**
Если речь идет о действии, требующем согласия, ты создаешь **задачу-действие** ТОЛЬКО ПОСЛЕ того, как обе стороны явно согласились.

- **Сценарий:**
  - Клиент: "Давайте созвонимся завтра в 3?"
  - Менеджер: "**Да, хорошо**, в 3 часа дня мне удобно."
  - → Твоё действие: `add_task("**Созвониться** с клиентом", due_date="2025-08-02 15:00:00", priority="high")`

- **Сценарий:**
  - Клиент: "Жду от вас подборку к вечеру."
  - Менеджер: "**Ок, подготовлю**."
  - → Твоё действие: `add_task("**Подготовить и отправить** подборку клиенту", due_date="{current_time.split(' ')[0]} 19:00:00", priority="high")`

---

### ТВОЙ РАБОЧИЙ ПРОЦЕСС (АЛГОРИТМ)

1.  **Проанализируй** последние сообщения в переписке.
2.  **Сравни** извлеченную информацию с текущим списком задач.
3.  **Прими решение на основе ГЛАВНОГО ПРИНЦИПА:**
    - Это **факт** или **подтвержденная договоренность**? → Сформулируй **задачу-действие** и создай ее через `add_task()`.
    - Это **предложение** от одной из сторон, еще не подтвержденное другой? → **Игнорируй.**
    - **Детали** существующей договоренности **изменились** (и обе стороны это подтвердили)? → Обнови задачу через `update_task()`, сохранив глагольный формат.
    - Задача **очевидно выполнена**? → Отметь ее как выполненную через `complete_task()`.
    - Договоренность **отменена**? → Удали задачу через `delete_task()`.
    - **Ничего не изменилось**? → Сразу переходи к шагу 5.
4.  **Выполни** необходимые вызовы инструментов.
5.  **Подтверди завершение.** Когда список задач полностью соответствует всем **финальным** договоренностям, вызови `confirm_all_tasks()`. **Это ОБЯЗАТЕЛЬНЫЙ финальный шаг.**

---

### ИНСТРУМЕНТЫ И ПАРАМЕТРЫ

- `add_task(description, due_date, priority)`
- `update_task(task_id, description?, due_date?, priority?)`
- `complete_task(task_id)`
- `delete_task(task_id)`
- `confirm_all_tasks()`

- `description`: **ОБЯЗАТЕЛЬНО в виде глагольного действия!** (Примеры: "Позвонить клиенту", "Отправить документы", "Уточнить детали").
- `due_date`: Срок в формате `YYYY-MM-DD HH:MM:SS`. Если время не указано, система установит 8:00 утра по умолчанию.
- `priority`: Приоритет - `"high"`, `"normal"`, `"low"`.

---

{tasks_info}
{manual_info}

Текущая дата и время: {current_time}
"""
    

    
    def analyze(self, client_id: int, client_name: str, chat_messages: List[Message]) -> Dict[str, Any]:
        """Запуск анализа задач"""
        formatted_messages = self._format_chat_messages(chat_messages)
        
        initial_state: TaskAnalysisState = {
            "client_id": client_id,
            "client_name": client_name,
            "messages": formatted_messages,
            "current_tasks": [],
            "manual_modifications": {},
            "new_tasks": [],
            "updated_tasks": [],
            "completed_task_ids": [],
            "deleted_task_ids": [],
            "confirmed": False,
            "errors": []
        }
        
        result = self.graph.invoke(initial_state)
        
        return {
            "new_tasks": result["new_tasks"],
            "updated_tasks": result["updated_tasks"],
            "completed_task_ids": result["completed_task_ids"],
            "deleted_task_ids": result["deleted_task_ids"],
            "confirmed": result["confirmed"],
            "errors": result["errors"]
        }


# Глобальный экземпляр агента
task_agent = TaskAnalysisAgent() 