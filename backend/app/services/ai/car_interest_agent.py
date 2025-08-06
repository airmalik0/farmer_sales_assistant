"""Агент для анализа автомобильных интересов клиента"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Optional

from ...core.database import SessionLocal
from ...models.car_interest import CarInterest
from ...models.message import Message
from .base_agent import BaseAnalysisAgent
from .tools import CAR_INTEREST_TOOLS

logger = logging.getLogger(__name__)


class CarInterestAnalysisState(TypedDict):
    """Состояние для анализа автомобильных интересов"""
    client_id: int
    client_name: str
    messages: List
    current_interests: Optional[List[Dict[str, Any]]]
    manual_modifications: Optional[Dict[str, Any]]
    updates: Dict[str, Any]
    confirmed: bool
    errors: List[str]


class CarInterestAnalysisAgent(BaseAnalysisAgent):
    """Агент для анализа автомобильных интересов"""
    
    def __init__(self):
        super().__init__(CAR_INTEREST_TOOLS, CarInterestAnalysisState)
    
    def _prepare_context(self, state: CarInterestAnalysisState) -> CarInterestAnalysisState:
        """Подготовка контекста для анализа"""
        logger.info(f"Подготовка контекста автомобильных интересов для клиента {state['client_id']}")
        
        # Получаем текущие интересы из БД
        db = SessionLocal()
        try:
            car_interest = db.query(CarInterest).filter(CarInterest.client_id == state['client_id']).first()
            if car_interest and car_interest.structured_data:
                state["current_interests"] = car_interest.structured_data.get("queries", [])
                state["manual_modifications"] = car_interest.structured_data.get("manual_modifications", {})
            else:
                state["current_interests"] = []
                state["manual_modifications"] = {}
        finally:
            db.close()
        
        state["updates"] = {}
        state["confirmed"] = False
        state["errors"] = []
        
        return state
    
    def _generate_system_prompt(self, state) -> str:
        """Генерация system prompt для анализа автомобильных интересов"""
        return self._generate_car_interest_prompt(
            state["client_name"],
            state["current_interests"],
            state["manual_modifications"],
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    
    def _process_updates(self, state: CarInterestAnalysisState) -> CarInterestAnalysisState:
        """Обработка обновлений из вызовов инструментов"""
        state["updates"] = {
            "add_queries": [],
            "update_queries": [],
            "delete_indices": []
        }
        
        # Проверяем tool_calls
        for message in reversed(state["messages"]):
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call["name"] == "add_car_interest_query":
                        # Собираем все аргументы в объект query
                        args = tool_call["args"]
                        query = {k: v for k, v in args.items() if v is not None and k != "index"}
                        if query:  # Добавляем только если есть хотя бы один аргумент
                            state["updates"]["add_queries"].append(query)
                    
                    elif tool_call["name"] == "update_car_interest_query":
                        if "index" in tool_call["args"]:
                            args = tool_call["args"]
                            query = {k: v for k, v in args.items() if v is not None and k != "index"}
                            if query:  # Добавляем только если есть аргументы для обновления
                                state["updates"]["update_queries"].append({
                                    "index": args["index"],
                                    "query": query
                                })
                    
                    elif tool_call["name"] == "delete_car_interest_query":
                        if "index" in tool_call["args"]:
                            state["updates"]["delete_indices"].append(tool_call["args"]["index"])
                    
                    elif tool_call["name"] == "confirm_all_car_interests":
                        state["confirmed"] = True
        
        return state
    
    def _generate_car_interest_prompt(self, client_name: str, current_interests: List[Dict],
                                     manual_modifications: Dict, current_time: str) -> str:
        """Создает промпт для анализа и фиксации автомобильных интересов клиента."""

        interests_info = "**Текущие автомобильные интересы клиента:**\n"
        if current_interests:
            for i, query in enumerate(current_interests):
                # Добавляем индекс прямо в вывод для наглядности
                interest_data = {"index": i, **query}
                interests_info += f"- {json.dumps(interest_data, ensure_ascii=False, indent=2)}\n"
        else:
            interests_info = "**Текущие автомобильные интересы:** нет сохраненных интересов\n"

        manual_info = ""
        if manual_modifications:
            manual_fields = []
            for field_path, info in manual_modifications.items():
                # Обрабатываем ключи формата "queries.{index}.{field}"
                if field_path.startswith("queries."):
                    parts = field_path.split(".")
                    if len(parts) >= 3:
                        index = parts[1]
                        field = parts[2]
                        modified_at = info.get('modified_at', info.get('updated_at', 'неизвестно'))
                        manual_fields.append(f"- Запрос {index}, поле {field}: изменено {modified_at}")
            if manual_fields:
                manual_info = f"""
⚠️ **ПОЛЯ, ИЗМЕНЕННЫЕ ВРУЧНУЮ:**
{chr(10).join(manual_fields)}
Обновляй их, только если клиент САМ прямо написал об изменении этих параметров."""

        return f"""Ты — ИИ-аналитик в автодилерской компании. Твоя задача — проанализировать переписку с клиентом {client_name} и точно зафиксировать его автомобильные интересы в виде структурированных запросов.

**КРИТИЧЕСКИ ВАЖНО**: Ты можешь взаимодействовать ТОЛЬКО через вызов инструментов (tools). НЕ пиши текстовые сообщения, только вызывай инструменты.

### ТВОЯ ГЛАВНАЯ ЦЕЛЬ
Поддерживать список автомобильных интересов клиента в АКТУАЛЬНОМ состоянии. Каждый объект в списке — это отдельный, независимый поиск автомобиля (например, клиент может одновременно искать и седан для себя, и внедорожник для жены).

---

### КЛЮЧЕВЫЕ ПРИНЦИПЫ РАБОТЫ

1.  **Один конкретный поиск = Один запрос.** Если клиент ищет "BMW X5 или Audi Q7", это ДВА разных запроса. Создай `add_car_interest_query` для BMW X5 и еще один для Audi Q7.
2.  **Новая информация обновляет старую.** Если последний запрос клиента противоречит старому, обнови старый запрос с помощью `update_car_interest_query`, а не создавай новый. Самые свежие сообщения от клиента имеют наивысший приоритет.
3.  **Конкретизация — это ОБНОВЛЕНИЕ.** Если клиент сначала искал "BMW до $50k", а потом уточнил "BMW X5 2022 года до $50k", ты должен ОБНОВИТЬ существующий запрос, а не создавать новый.
4.  **Игнорируй нечеткие запросы.** Фразы вроде "посмотрю варианты", "что посоветуете?", "ищу что-то надежное" НЕ являются основанием для создания или изменения запроса. Фиксируй только конкретные параметры.
5.  **Не дублируй.** Прежде чем вызывать `add_car_interest_query`, убедись, что абсолютно такого же запроса еще нет в списке.

---

### ФОРМАТ ЗАПРОСА (JSON-объект)
Используй эти поля при вызове инструментов. Всегда нормализуй данные.

- `brand`: Марка автомобиля (строка). Нормализуй: "бмв" -> "BMW".
- `model`: Модель автомобиля (строка). Нормализуй: "х5" -> "X5".
- `price_min`, `price_max`: Бюджет в USD. Извлекай только числа: "до 65к$" -> `price_max: 65000`.
- `year_min`, `year_max`: Год выпуска.
- `mileage_max`: Максимальный пробег в КИЛОМЕТРАХ.
- `exterior_color`, `interior_color`: Цвет (строка). Если несколько цветов, указывай основной.
- `engine_type`: тип двигателя "gas", "diesel", "hybrid", "electric".
- `drive_type`: привод "AWD", "FWD", "RWD".
- `notes`: Короткий комментарий для дополнительных требований (например: "только с панорамой, исключить красный цвет").

---

### ТВОЙ РАБОЧИЙ ПРОЦЕСС (АЛГОРИТМ):

1. **Проанализируй** последние сообщения в переписке.
2. **Сравни** извлеченную информацию с текущим списком интересов.
3. **Прими решение:**
   - Есть **новая информация** или **изменения**? → Обнови только измененные/новые запросы
   - **Ничего не изменилось** и не добавилось? → Сразу переходи к шагу 5
4. **Выполни** обновления для каждого измененного запроса и дождись результатов.
5. **Подтверди завершение.** Когда список интересов полностью соответствует переписке, вызови `confirm_all_car_interests()`. **Это ОБЯЗАТЕЛЬНЫЙ финальный шаг.** Без него твоя работа не будет засчитана.

---
**При использовании `update_car_interest_query` передавай ВСЕ поля запроса, даже если они не изменились!**
Если ты не передашь какое-то поле при обновлении, система ОЧИСТИТ это поле (установит в null).
---

{interests_info}
{manual_info}

Текущая дата и время: {current_time}
"""
    
    def analyze(self, client_id: int, client_name: str, chat_messages: List[Message]) -> Dict[str, Any]:
        """Запуск анализа автомобильных интересов"""
        formatted_messages = self._format_chat_messages(chat_messages)
        
        initial_state: CarInterestAnalysisState = {
            "client_id": client_id,
            "client_name": client_name,
            "messages": formatted_messages,
            "current_interests": [],
            "manual_modifications": {},
            "updates": {},
            "confirmed": False,
            "errors": []
        }
        
        result = self.graph.invoke(initial_state)
        
        return {
            "updates": result["updates"],
            "confirmed": result["confirmed"],
            "errors": result["errors"]
        }


# Глобальный экземпляр агента
car_interest_agent = CarInterestAnalysisAgent() 