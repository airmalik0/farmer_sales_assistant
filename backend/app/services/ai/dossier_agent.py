"""Агент для анализа досье клиента"""

import logging
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Optional
from sqlalchemy.orm import Session

from ...core.database import SessionLocal
from ...models.dossier import Dossier
from ...models.message import Message
from .base_agent import BaseAnalysisAgent
from .tools import DOSSIER_TOOLS

logger = logging.getLogger(__name__)


class DossierAnalysisState(TypedDict):
    """Состояние для анализа досье"""
    client_id: int
    client_name: str
    messages: List
    current_dossier: Optional[Dict[str, Any]]
    manual_modifications: Optional[Dict[str, Any]]
    updates: Dict[str, Any]
    confirmed: bool
    errors: List[str]


class DossierAnalysisAgent(BaseAnalysisAgent):
    """Агент для анализа досье клиента"""
    
    def __init__(self):
        super().__init__(DOSSIER_TOOLS, DossierAnalysisState)
    
    def _get_field_display_name(self, field: str) -> str:
        """Возвращает отображаемое название поля"""
        field_names = {
            'phone': 'Телефон',
            'current_location': 'Местоположение', 
            'birthday': 'Дата рождения',
            'gender': 'Пол',
            'client_type': 'Тип клиента',
            'personal_notes': 'Личные заметки',
            'business_profile': 'Бизнес-профиль'
        }
        return field_names.get(field, field)
    
    def _prepare_context(self, state: DossierAnalysisState) -> DossierAnalysisState:
        """Подготовка контекста для анализа"""
        logger.info(f"Подготовка контекста досье для клиента {state['client_id']}")
        
        # Получаем текущее досье из БД
        db = SessionLocal()
        try:
            dossier = db.query(Dossier).filter(Dossier.client_id == state['client_id']).first()
            if dossier and dossier.structured_data:
                # Извлекаем данные клиента
                if "client_info" in dossier.structured_data:
                    client_info = dossier.structured_data["client_info"]
                    state["current_dossier"] = {
                        "phone": client_info.get("phone"),
                        "current_location": client_info.get("current_location"),
                        "birthday": client_info.get("birthday"),
                        "gender": client_info.get("gender"),
                        "client_type": client_info.get("client_type"),
                        "personal_notes": client_info.get("personal_notes"),
                        "business_profile": client_info.get("business_profile")
                    }
                else:
                    state["current_dossier"] = None
                
                # Извлекаем manual_modifications
                state["manual_modifications"] = dossier.structured_data.get("manual_modifications", {})
            else:
                state["current_dossier"] = None
                state["manual_modifications"] = {}
        finally:
            db.close()
        
        state["updates"] = {}
        state["confirmed"] = False
        state["errors"] = []
        
        return state
    
    def _generate_system_prompt(self, state) -> str:
        """Генерация system prompt для анализа досье"""
        return self._generate_dossier_prompt(
            state["client_name"],
            state["current_dossier"],
            state["manual_modifications"],
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    
    def _process_updates(self, state: DossierAnalysisState) -> DossierAnalysisState:
        """Обработка обновлений из вызовов инструментов"""
        # Ищем вызовы инструментов в последних сообщениях
        for message in reversed(state["messages"]):
            if hasattr(message, "content") and isinstance(message.content, str):
                # Проверяем результаты вызовов инструментов
                if "будет обновлено на значение:" in message.content:
                    # Извлекаем field и value из сообщения
                    parts = message.content.split("'")
                    if len(parts) >= 4:
                        field = parts[1]
                        value_part = message.content.split("значение: ")
                        if len(value_part) > 1:
                            value = value_part[1].strip()
                            # Преобразуем "None" в None
                            if value == "None":
                                value = None
                            
                            # Проверяем что значение действительно изменилось
                            current_value = state["current_dossier"].get(field) if state["current_dossier"] else None
                            if value != current_value:
                                state["updates"][field] = value
                            else:
                                logger.info(f"Пропускаем обновление поля '{field}' - значение не изменилось")
                
                elif "Все поля досье подтверждены" in message.content:
                    state["confirmed"] = True
        
        # Проверяем tool_calls для более точного извлечения данных
        for message in reversed(state["messages"]):
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call["name"] == "update_dossier_field":
                        field = tool_call["args"]["field"]
                        value = tool_call["args"]["value"]
                        
                        # Проверяем что значение действительно изменилось
                        current_value = state["current_dossier"].get(field) if state["current_dossier"] else None
                        if value != current_value:
                            state["updates"][field] = value
                        else:
                            logger.info(f"Пропускаем обновление поля '{field}' - значение не изменилось")
                    
                    elif tool_call["name"] == "confirm_all_dossier":
                        state["confirmed"] = True
        
        return state
    
    def _generate_dossier_prompt(self, client_name: str, current_dossier: Optional[Dict], 
                                 manual_modifications: Dict, current_time: str) -> str:
        """Создает промпт для анализа досье клиента автодилера с учетом его типа."""

        # Форматирование текущего досье
        dossier_info = ""
        if current_dossier:
            dossier_info = f"""
**Текущая информация о клиенте:**
- Телефон: {current_dossier.get('phone', 'не указан')}
- Регион работы/проживания: {current_dossier.get('current_location', 'не указано')}
- Дата рождения: {current_dossier.get('birthday', 'не указана')}
- Пол: {current_dossier.get('gender', 'не указан')}
- Тип клиента: {current_dossier.get('client_type', 'не определен')}
- Личные заметки: {current_dossier.get('personal_notes', 'не заполнено')}
- Бизнес-профиль: {current_dossier.get('business_profile', 'не заполнен')}"""

        # Информация о защищенных полях
        protected_info = ""
        if manual_modifications:
            protected_fields = [self._get_field_display_name(f) for f in manual_modifications.keys()]
            protected_info = f"\n⚠️ Поля {', '.join(protected_fields)} подтверждены вручную - обновляй только при явных изменениях в переписке."

        return f"""Ты — ИИ-ассистент в автодилерской компании, которая привозит машины из США.
Твоя задача — проанализировать переписку с клиентом {client_name} и составить на него подробное досье.

**КРИТИЧЕСКИ ВАЖНО**: Ты можешь взаимодействовать ТОЛЬКО через вызов инструментов (tools). НЕ пиши текстовые сообщения, только вызывай инструменты.

**ТВОЯ ГЛАВНАЯ ЦЕЛЬ:**
Собрать ключевую информацию, которая поможет менеджеру строить долгосрочные отношения с клиентом и предлагать ему наиболее подходящие варианты.

---

### **ШАГ 1: Определи тип клиента**

**Типы клиентов (`client_type`):**
- **private**: "Частник" (покупает для себя, личного пользования)
- **reseller**: "Перекуп" (покупает для быстрой перепродажи)
- **broker**: "Автоподборщик" (работает под конкретный заказ конечного клиента)
- **dealer**: "Дилер" (имеет свой автосалон или площадку)
- **transporter**: "Перегонщик" (специализируется на логистике и доставке)

---

### **ШАГ 2: Собери информацию для досье**
Внимательно прочитай ВСЮ переписку и последовательно заполняй поля, вызывая `update_dossier_field(поле, значение)` для каждого нового факта.

**1. Основные данные (для всех):**
- **phone**: актуальный телефон для связи.
- **current_location**: город/страна, где клиент проживает или ведет бизнес.
- **birthday**: дата рождения в формате YYYY-MM-DD (только если прямо указана).
- **gender**: "male" или "female" (только если однозначно понятно).

**2. Личные заметки (`personal_notes`) (для всех):**
Сюда нужно записывать информацию, которая помогает наладить личный контакт. Это важно для **всех** типов клиентов.
✓ Семейное положение, наличие детей (например: "ищет авто для семьи, трое детей")
✓ Наличие домашних животных (например: "есть большая собака, важен просторный багажник")
✓ Хобби, увлечения, связанные с авто (например: "любит дрифт", "ездит на рыбалку")
✓ Планы на переезд, смену работы (например: "планирует переезд в другой регион")
✓ Важные личные предпочтения (например: "не любит красный цвет", "принципиально только кожаный салон")

**3. Бизнес-профиль (`business_profile`) (ТОЛЬКО для `reseller`, `broker`, `dealer`):**
**Заполняй это поле, только если тип клиента НЕ `private`.** Это ключевая информация о его профессиональной деятельности.
✓ Специализация (например: "работает с внедорожниками до 30к", "возит битки под восстановление")
✓ Объемы закупок (например: "берет 2-3 авто в месяц", "ищет партнера на 10+ авто/мес")
✓ Особые требования (например: "только чистые карфаксы", "работает с Copart и IAAI")
✓ Ценовой сегмент (например: "бюджет 15-20к", "премиум от 50к")
✓ Ключевые договоренности (например: "скидка 500$ от 3 авто")

---

### **ТВОЙ РАБОЧИЙ ПРОЦЕСС (АЛГОРИТМ):**

1. **Проанализируй** последние сообщения в переписке.
2. **Сравни** извлеченную информацию с текущим досье.
3. **Прими решение:**
   - Есть **новая информация** или **изменения**? → Обнови только измененные поля через `update_dossier_field(поле, значение)`
   - **Ничего не изменилось** и не добавилось? → Сразу переходи к шагу 5
4. **Выполни** обновления для каждого измененного поля и дождись результатов.
5. **Подтверди завершение.** Когда досье полностью соответствует переписке, вызови `confirm_all_dossier()`. **Это ОБЯЗАТЕЛЬНЫЙ финальный шаг.** Без него твоя работа не будет засчитана.

---

### **ОБЩИЕ ПРАВИЛА И ИНСТРУКЦИИ:**
- **Фокусируйся на стабильной информации.** Игнорируй сиюминутные детали ("сейчас в дороге", "подумаю до вечера").
- **Не записывай очевидные вещи** ("интересуется ценами", "отвечает на сообщения") и стилистику общения.
- **Если информация неоднозначна — лучше не записывать**, чтобы не вводить менеджера в заблуждение.

Твоя работа напрямую влияет на качество и скорость сделок. Будь внимателен.

---

{dossier_info}{protected_info}

Текущее время: {current_time}
"""
    
    def analyze(self, client_id: int, client_name: str, chat_messages: List[Message]) -> Dict[str, Any]:
        """Запуск анализа досье"""
        formatted_messages = self._format_chat_messages(chat_messages)
        
        initial_state: DossierAnalysisState = {
            "client_id": client_id,
            "client_name": client_name,
            "messages": formatted_messages,
            "current_dossier": None,
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
dossier_agent = DossierAnalysisAgent() 