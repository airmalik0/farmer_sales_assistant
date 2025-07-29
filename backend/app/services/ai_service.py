from openai import OpenAI
from typing import List
from datetime import datetime, timedelta
import threading
from threading import Timer
import time
import logging
import asyncio
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import SessionLocal
from ..models.message import Message
from ..models.client import Client
from .message_service import MessageService
from .dossier_service import DossierService
from .car_interest_service import CarInterestService
from .task_service import TaskService
import json

# Настройка логирования для отслеживания background задач
logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.openai_api_key)

# JSON схема для structured output (единый стиль)
DOSSIER_SCHEMA = {
    "type": "object",
    "properties": {
        "client_info": {
            "type": "object",
            "properties": {
                "phone": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Номер телефона клиента"
                },
                "current_location": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Город или местоположение клиента"
                },
                "birthday": {
                    "anyOf": [{"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}, {"type": "null"}],
                    "description": "Дата рождения в формате YYYY-MM-DD"
                },
                "gender": {
                    "anyOf": [{"type": "string", "enum": ["male", "female"]}, {"type": "null"}],
                    "description": "Пол клиента: male или female"
                },
                "notes": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Дополнительные неструктурированные заметки о клиенте"
                }
            },
            "required": ["phone", "current_location", "birthday", "gender", "notes"],
            "additionalProperties": False
        }
    },
    "required": ["client_info"],
    "additionalProperties": False
}

# JSON схема для задач
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "description": "Список задач, которые нужно выполнить",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Четкое описание задачи"
                    },
                    "due_date": {
                        "anyOf": [{"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}, {"type": "null"}],
                        "description": "Дата выполнения задачи в формате YYYY-MM-DD. Null, если дата не определена."
                    },
                    "priority": {
                        "anyOf": [{"type": "string", "enum": ["low", "normal", "high"]}, {"type": "null"}],
                        "description": "Приоритет задачи: low, normal или high. По умолчанию normal."
                    }
                },
                "required": ["description", "due_date", "priority"],
                "additionalProperties": False
            }
        }
    },
    "required": ["tasks"],
    "additionalProperties": False
}

# JSON схема для автомобильных интересов (единый стиль)
CAR_INTEREST_SCHEMA = {
    "type": "object",
    "properties": {
        "queries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "brand": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "null"}
                        ],
                        "description": "Марка автомобиля или массив марок"
                    },
                    "model": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "null"}
                        ],
                        "description": "Модель автомобиля или массив моделей"
                    },
                    "price_min": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Минимальная цена в долларах"
                    },
                    "price_max": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Максимальная цена в долларах"
                    },
                    "year_min": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Минимальный год выпуска"
                    },
                    "year_max": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Максимальный год выпуска"
                    },
                    "mileage_max": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Максимальный пробег в км"
                    },
                    "exterior_color": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "null"}
                        ],
                        "description": "Цвет кузова или массив цветов"
                    },
                    "interior_color": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "null"}
                        ],
                        "description": "Цвет салона или массив цветов"
                    }
                },
                "required": ["brand", "model", "price_min", "price_max", "year_min", "year_max", "mileage_max", "exterior_color", "interior_color"],
                "additionalProperties": False
            }
        }
    },
    "required": ["queries"],
    "additionalProperties": False
}


def send_dossier_notification(client_id: int, dossier_data: dict):
    """Отправка уведомления о досье из фонового процесса"""
    try:
        # Импортируем здесь чтобы избежать циклических импортов
        from ..api.websocket import notify_dossier_update
        
        # Создаем новый event loop для отправки уведомления
        # Это безопасно в фоновых задачах (Timer)
        import asyncio
        
        async def _send_notification():
            await notify_dossier_update(client_id, dossier_data)
        
        # Создаем новый loop и запускаем уведомление
        asyncio.run(_send_notification())
        
        logger.info(f"WebSocket уведомление о досье отправлено для клиента {client_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки WebSocket уведомления о досье: {e}")
        # Продолжаем работу даже если уведомление не отправилось


def send_car_interest_notification(client_id: int, car_interest_data: dict):
    """Отправка уведомления о автомобильных интересах из фонового процесса"""
    try:
        # Импортируем здесь чтобы избежать циклических импортов
        from ..api.websocket import notify_car_interest_update
        
        # Создаем новый event loop для отправки уведомления
        # Это безопасно в фоновых задачах (Timer)
        import asyncio
        
        async def _send_notification():
            await notify_car_interest_update(client_id, car_interest_data)
        
        # Создаем новый loop и запускаем уведомление
        asyncio.run(_send_notification())
        
        logger.info(f"WebSocket уведомление о автомобильных интересах отправлено для клиента {client_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки WebSocket уведомления о автомобильных интересах: {e}")
        # Продолжаем работу даже если уведомление не отправилось


def send_task_notification(client_id: int, task_data: dict):
    """Отправка уведомления о задачах из фонового процесса"""
    try:
        # Импортируем здесь чтобы избежать циклических импортов
        from ..api.websocket import notify_task_update
        
        # Создаем новый event loop для отправки уведомления
        # Это безопасно в фоновых задачах (Timer)
        import asyncio
        
        async def _send_notification():
            await notify_task_update(client_id, task_data)
        
        # Создаем новый loop и запускаем уведомление
        asyncio.run(_send_notification())
        
        logger.info(f"WebSocket уведомление о задачах отправлено для клиента {client_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки WebSocket уведомления о задачах: {e}")
        # Продолжаем работу даже если уведомление не отправилось


class ClientAnalysisTimers:
    """Управление таймерами анализа для каждого клиента"""
    def __init__(self):
        self._timers = {}
        self._lock = threading.Lock()
    
    def schedule(self, client_id: int, callback, delay_seconds: float):
        """Запланировать анализ для клиента, отменив предыдущий таймер если есть"""
        with self._lock:
            # Отменяем старый таймер если существует
            if client_id in self._timers:
                old_timer = self._timers[client_id]
                old_timer.cancel()
                logger.info(f"Отменен предыдущий таймер для клиента {client_id}")
            
            # Создаем новый таймер
            timer = Timer(delay_seconds, callback)
            timer.daemon = True
            timer.start()
            self._timers[client_id] = timer
            logger.info(f"Запланирован анализ для клиента {client_id} через {delay_seconds/60:.1f} минут")
    
    def cancel(self, client_id: int):
        """Отменить запланированный анализ для клиента"""
        with self._lock:
            if client_id in self._timers:
                self._timers[client_id].cancel()
                del self._timers[client_id]
                logger.info(f"Отменен таймер для клиента {client_id}")


# Глобальный экземпляр для управления таймерами
analysis_timers = ClientAnalysisTimers()


class AIService:
    @staticmethod
    def format_chat_history(messages: List[Message]) -> str:
        """Форматирует историю чата для анализа AI"""
        formatted_messages = []
        for msg in messages:
            sender = "Клиент" if msg.sender.value == "client" else "Менеджер"
            content = msg.content
            
            # Добавляем информацию о типе контента
            if msg.content_type != "text":
                content = f"[{msg.content_type.upper()}] {content}"
            
            formatted_messages.append(f"{sender}: {content}")
        
        return "\n".join(formatted_messages)

    @staticmethod
    def generate_dossier_prompt(chat_history: str, client_name: str) -> str:
        """Создает промпт для генерации досье клиента"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""
Твоя задача — проанализировать переписку с клиентом `{client_name}` и на её основе сгенерировать JSON с информацией о клиенте.

**Переписка:**
{chat_history}

---

**ИНСТРУКЦИЯ:**

Собери всю информацию о клиенте и заполни поля в объекте `client_info`.

* **phone** - номер телефона клиента, если упоминается
* **current_location** - город или местоположение клиента
* **birthday** - дата рождения в формате YYYY-MM-DD, если упоминается
* **gender** - пол клиента (male/female), если можно определить
* **notes** - важные факты о клиенте: детали о семье, хобби, прошлый опыт владения авто, предпочтения, особенности характера и т.д.

* Если какая-то информация не упоминается в переписке, используй `null` для этого поля.
* В `notes` записывай только фактическую информацию о клиенте, не включай задачи или действия для менеджера.

Твой ответ должен быть **только** в формате JSON, соответствующем предоставленной схеме.
**Текущая дата и время: {current_time}**
"""

    @staticmethod
    def generate_car_interest_prompt(chat_history: str, client_name: str) -> str:
        """Создает промпт для анализа автомобильных интересов клиента"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""
Ты — экспертный ассистент для менеджера по продажам в автосалоне. Твоя задача — анализировать переписку с клиентом `{client_name}` и извлекать его требования к автомобилю в строгом JSON-формате. Вся информация должна быть нормализована: "бмв" -> "BMW", "х5" -> "X5".

**Правила формирования JSON:**

1. Основной ключ — "queries", который является массивом. Каждый элемент массива — это отдельный набор фильтров для поиска. Эти наборы работают по принципу "ИЛИ".
2. Внутри каждого объекта в массиве все поля работают по принципу "И": brand И model И price_max и т.д.
3. Все поля необязательны. Если клиент не указал параметр, не добавляй это поле в объект.
4. Для параметров brand, model, exterior_color, interior_color используй массив строк, если клиент указал несколько вариантов в рамках ОДНОГО запроса (например, "черный или белый кузов").
5. Извлекай только числа для цен и пробега. "65к$" или "65 тысяч долларов" должно стать 65000.
6. Всегда выводи только JSON-объект и ничего больше. Никаких комментариев, объяснений или приветствий.
7. Если информации в запросе недостаточно для формирования фильтра или запрос не относится к поиску авто, верни пустой массив: {{"queries": []}}.

**Переписка:**
{chat_history}

Проанализируй переписку и извлеки автомобильные интересы клиента в указанном JSON-формате.

Текущая дата и время: {current_time}
"""

    @staticmethod
    def generate_task_prompt(chat_history: str, client_name: str) -> str:
        """Создает промпт для анализа задач клиента"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""
Твоя задача — проанализировать переписку с клиентом `{client_name}` и создать список задач для менеджера по продажам.

**Переписка:**
{chat_history}

---

**ИНСТРУКЦИЯ:**

Внимательно прочти переписку и определи все действия, которые должен совершить менеджер. Каждая задача — это отдельный объект в массиве `tasks`.

**Типы задач:**

* **Задачи с конкретной датой:**
    * Если договорились о звонке/встрече ("созвонимся завтра", "встреча в среду"), вычисли точную дату на основе `{current_time}` и укажи ее в `due_date`.
    * Если клиент упоминает событие ("лечу в Москву завтра"), создай задачу на день после события ("Поинтересоваться, как прошёл полёт").
    * Если известен день рождения клиента, создай задачу "Поздравить с днём рождения" на **ближайшую** дату его дня рождения.
    * Срочные задачи получают приоритет "high", плановые встречи/звонки - "normal", долгосрочные напоминания - "low".

* **Задачи без даты (`due_date: null`):**
    * Если клиент ищет автомобиль, которого нет в наличии, создай задачу без даты. Например: "Когда приедет BMW X5 - уведомить".
    * Общие напоминания о клиенте.

* **Приоритеты:**
    * "high" - срочные задачи, звонки "сегодня", "завтра"
    * "normal" - плановые встречи, звонки через несколько дней
    * "low" - долгосрочные напоминания, дни рождения

**Если задач нет**, оставь массив `tasks` пустым: `[]`.

Твой ответ должен быть **только** в формате JSON, соответствующем предоставленной схеме.
**Текущая дата и время: {current_time}**
"""

    @staticmethod
    def generate_car_interest(chat_history: str, client_name: str) -> str:
        """Генерирует автомобильные интересы клиента с помощью OpenAI structured output"""
        try:
            prompt = AIService.generate_car_interest_prompt(chat_history, client_name)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты эксперт по анализу автомобильных требований клиентов. Извлекай фильтры поиска автомобилей из переписок в строгом JSON-формате."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "car_interest",
                        "description": "Автомобильные интересы клиента с извлеченными фильтрами поиска",
                        "schema": CAR_INTEREST_SCHEMA,
                        "strict": True
                    }
                }
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка при генерации автомобильных интересов: {e}")
            return f"Ошибка анализа: {str(e)}"

    @staticmethod
    def generate_tasks(chat_history: str, client_name: str) -> str:
        """Генерирует задачи для клиента с помощью OpenAI structured output"""
        try:
            prompt = AIService.generate_task_prompt(chat_history, client_name)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты эксперт по анализу клиентского взаимодействия. Создавай задачи для менеджеров по продажам на основе переписок с клиентами."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "client_tasks",
                        "description": "Задачи для менеджера по работе с клиентом",
                        "schema": TASK_SCHEMA,
                        "strict": True
                    }
                }
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка при генерации задач: {e}")
            return f"Ошибка анализа: {str(e)}"

    @staticmethod
    def generate_dossier(chat_history: str, client_name: str) -> str:
        """Генерирует досье клиента с помощью OpenAI structured output"""
        try:
            prompt = AIService.generate_dossier_prompt(chat_history, client_name)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты эксперт по анализу клиентского взаимодействия. Извлекай информацию о клиентах из переписок."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "client_dossier",
                        "description": "Досье клиента с извлеченной информацией",
                        "schema": DOSSIER_SCHEMA,
                        "strict": True
                    }
                }
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка при генерации досье: {e}")
            return f"Ошибка анализа: {str(e)}"


    @staticmethod
    def analyze_client_dialogue_sync(client_id: int) -> str:
        """Синхронный анализ диалога клиента"""
        db = SessionLocal()
        try:
            logger.info(f"Начинаем анализ диалога для клиента {client_id}")
            
            # Получаем клиента
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.warning(f"Клиент {client_id} не найден")
                return f"Клиент {client_id} не найден"

            # Получаем историю чата
            messages = MessageService.get_chat_history(db, client_id)
            if not messages:
                logger.info(f"Нет сообщений для клиента {client_id}")
                return f"Нет сообщений для клиента {client_id}"

            # Форматируем историю
            chat_history = AIService.format_chat_history(messages)
            client_name = client.first_name or f"ID {client.telegram_id}"

            # Генерируем досье
            json_response = AIService.generate_dossier(chat_history, client_name)
            
            # Парсим JSON ответ
            try:
                structured_data = json.loads(json_response)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON ответа: {e}")
                return f"Ошибка парсинга ответа AI: {str(e)}"

            # Сохраняем структурированное досье
            dossier = DossierService.update_or_create_dossier(
                db, client_id, structured_data, 
                notify_callback=send_dossier_notification
            )
            
            result = f"Досье для клиента {client_name} обновлено"
            logger.info(result)
            return result
        
        except Exception as e:
            error_msg = f"Ошибка при анализе диалога клиента {client_id}: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()

    @staticmethod
    def analyze_client_car_interests_sync(client_id: int) -> str:
        """Синхронный анализ автомобильных интересов клиента"""
        db = SessionLocal()
        try:
            logger.info(f"Начинаем анализ автомобильных интересов для клиента {client_id}")
            
            # Получаем клиента
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.warning(f"Клиент {client_id} не найден")
                return f"Клиент {client_id} не найден"

            # Получаем историю чата
            messages = MessageService.get_chat_history(db, client_id)
            if not messages:
                logger.info(f"Нет сообщений для клиента {client_id}")
                return f"Нет сообщений для клиента {client_id}"

            # Форматируем историю
            chat_history = AIService.format_chat_history(messages)
            client_name = client.first_name or f"ID {client.telegram_id}"

            # Генерируем автомобильные интересы
            json_response = AIService.generate_car_interest(chat_history, client_name)
            
            # Парсим JSON ответ
            try:
                structured_data = json.loads(json_response)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON ответа автомобильных интересов: {e}")
                return f"Ошибка парсинга ответа AI: {str(e)}"

            # Сохраняем автомобильные интересы
            car_interest = CarInterestService.update_or_create_car_interest(
                db, client_id, structured_data, 
                notify_callback=send_car_interest_notification
            )
            
            result = f"Автомобильные интересы для клиента {client_name} обновлены"
            logger.info(result)
            return result
        
        except Exception as e:
            error_msg = f"Ошибка при анализе автомобильных интересов клиента {client_id}: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()

    @staticmethod
    def analyze_client_tasks_sync(client_id: int) -> str:
        """Синхронный анализ задач клиента"""
        db = SessionLocal()
        try:
            logger.info(f"Начинаем анализ задач для клиента {client_id}")
            
            # Получаем клиента
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.warning(f"Клиент {client_id} не найден")
                return f"Клиент {client_id} не найден"

            # Получаем историю чата
            messages = MessageService.get_chat_history(db, client_id)
            if not messages:
                logger.info(f"Нет сообщений для клиента {client_id}")
                return f"Нет сообщений для клиента {client_id}"

            # Форматируем историю
            chat_history = AIService.format_chat_history(messages)
            client_name = client.first_name or f"ID {client.telegram_id}"

            # Генерируем задачи
            json_response = AIService.generate_tasks(chat_history, client_name)
            
            # Парсим JSON ответ
            try:
                structured_data = json.loads(json_response)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON ответа задач: {e}")
                return f"Ошибка парсинга ответа AI: {str(e)}"

            # Извлекаем задачи из ответа
            tasks_data = structured_data.get('tasks', [])
            
            if tasks_data:
                # Создаем задачи
                created_tasks = TaskService.create_multiple_tasks(
                    db, client_id, tasks_data, 
                    notify_callback=send_task_notification
                )
                result = f"Создано {len(created_tasks)} задач для клиента {client_name}"
            else:
                result = f"Задачи для клиента {client_name} не найдены"
            
            logger.info(result)
            return result
        
        except Exception as e:
            error_msg = f"Ошибка при анализе задач клиента {client_id}: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()

    @staticmethod
    def schedule_analysis_after_delay(client_id: int, delay_minutes: int = 5):
        """Запланировать анализ диалога, автомобильных интересов и задач через указанное время"""
        def perform_analysis():
            try:
                logger.info(f"Выполняется анализ для клиента {client_id}")
                # Запускаем анализ досье
                AIService.analyze_client_dialogue_sync(client_id)
                # Запускаем анализ автомобильных интересов
                AIService.analyze_client_car_interests_sync(client_id)
                # Запускаем анализ задач
                AIService.analyze_client_tasks_sync(client_id)
            except Exception as e:
                logger.error(f"Ошибка при анализе клиента {client_id}: {e}")
        
        # Используем новый механизм таймеров
        delay_seconds = delay_minutes * 60
        analysis_timers.schedule(client_id, perform_analysis, delay_seconds)

