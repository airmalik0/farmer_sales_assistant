"""Тестовый скрипт для проверки работы агентов с tool calling"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List

# Устанавливаем переменные окружения для LangSmith ДО импорта агентов
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "farmer-crm-agents-test"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

print("\n" + "="*50)
print("🔍 LangSmith трейсинг ВКЛЮЧЕН!")
print(f"📊 Проект: farmer-crm-agents-test")
print(f"🔗 URL: https://smith.langchain.com/o/8ccfed96-3517-53ea-8c94-1dc19e3c4991/projects/p/farmer-crm-agents-test")
print("="*50 + "\n")

from app.models.message import Message, SenderType
from app.services.ai.task_agent import task_agent
from app.services.ai.dossier_agent import dossier_agent
from app.services.ai.car_interest_agent import car_interest_agent

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_messages() -> List[Message]:
    """Создает тестовые сообщения для проверки агентов"""
    messages = []
    
    # Сообщение от клиента
    msg1 = Message(
        client_id=1,
        sender=SenderType.client,
        content="Здравствуйте! Меня зовут Иван, я из Москвы. Ищу BMW X5 2022 года, бюджет до 65000$. У меня день рождения 15 января, может будет скидка? :)",
        content_type="text",
        income=True,
        timestamp=datetime.now()
    )
    messages.append(msg1)
    
    # Ответ менеджера
    msg2 = Message(
        client_id=1,
        sender=SenderType.farmer,
        content="Добрый день, Иван! Поздравляю заранее с днем рождения! Давайте подберем вам отличный BMW X5. Когда вам удобно созвониться для обсуждения деталей?",
        content_type="text",
        income=False,
        timestamp=datetime.now()
    )
    messages.append(msg2)
    
    # Ответ клиента
    msg3 = Message(
        client_id=1,
        sender=SenderType.client,
        content="Давайте созвонимся завтра в 15:00. Мне подойдет любой цвет, кроме красного. Желательно с панорамной крышей.",
        content_type="text",
        income=True,
        timestamp=datetime.now()
    )
    messages.append(msg3)
    
    # Подтверждение менеджера
    msg4 = Message(
        client_id=1,
        sender=SenderType.farmer,
        content="Отлично, договорились! Завтра в 15:00 созваниваемся. Подготовлю для вас варианты BMW X5 с панорамой.",
        content_type="text",
        income=False,
        timestamp=datetime.now()
    )
    messages.append(msg4)
    
    return messages


def test_task_agent():
    """Тестирует агента задач"""
    logger.info("=" * 50)
    logger.info("Тестирование Task Agent")
    logger.info("=" * 50)
    
    messages = create_test_messages()
    
    try:
        result = task_agent.analyze(
            client_id=1,
            client_name="Иван",
            chat_messages=messages
        )
        
        logger.info(f"Результат анализа задач:")
        logger.info(f"Новые задачи: {result.get('new_tasks', [])}")
        logger.info(f"Обновленные задачи: {result.get('updated_tasks', [])}")
        logger.info(f"Завершенные задачи: {result.get('completed_task_ids', [])}")
        logger.info(f"Удаленные задачи: {result.get('deleted_task_ids', [])}")
        logger.info(f"Подтверждено: {result.get('confirmed', False)}")
        logger.info(f"Ошибки: {result.get('errors', [])}")
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при тестировании Task Agent: {e}")
        return None


def test_dossier_agent():
    """Тестирует агента досье"""
    logger.info("=" * 50)
    logger.info("Тестирование Dossier Agent")
    logger.info("=" * 50)
    
    messages = create_test_messages()
    
    try:
        result = dossier_agent.analyze(
            client_id=1,
            client_name="Иван",
            chat_messages=messages
        )
        
        logger.info(f"Результат анализа досье:")
        logger.info(f"Обновления: {result.get('updates', {})}")
        logger.info(f"Подтверждено: {result.get('confirmed', False)}")
        logger.info(f"Ошибки: {result.get('errors', [])}")
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при тестировании Dossier Agent: {e}")
        return None


def test_car_interest_agent():
    """Тестирует агента автомобильных интересов"""
    logger.info("=" * 50)
    logger.info("Тестирование Car Interest Agent")
    logger.info("=" * 50)
    
    messages = create_test_messages()
    
    try:
        result = car_interest_agent.analyze(
            client_id=1,
            client_name="Иван",
            chat_messages=messages
        )
        
        logger.info(f"Результат анализа автомобильных интересов:")
        logger.info(f"Обновления: {result.get('updates', {})}")
        logger.info(f"Подтверждено: {result.get('confirmed', False)}")
        logger.info(f"Ошибки: {result.get('errors', [])}")
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при тестировании Car Interest Agent: {e}")
        return None


if __name__ == "__main__":
    # Тестируем каждого агента
    task_result = test_task_agent()
    print("\n")
    
    dossier_result = test_dossier_agent()
    print("\n")
    
    car_interest_result = test_car_interest_agent()
    
    # Итоговая статистика
    logger.info("=" * 50)
    logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
    logger.info("=" * 50)
    
    # Проверяем что агенты использовали только tools
    all_confirmed = True
    if task_result:
        if task_result.get('confirmed'):
            logger.info("✅ Task Agent успешно завершил работу через tools")
        else:
            logger.warning("⚠️ Task Agent не подтвердил завершение")
            all_confirmed = False
    
    if dossier_result:
        if dossier_result.get('confirmed'):
            logger.info("✅ Dossier Agent успешно завершил работу через tools")
        else:
            logger.warning("⚠️ Dossier Agent не подтвердил завершение")
            all_confirmed = False
    
    if car_interest_result:
        if car_interest_result.get('confirmed'):
            logger.info("✅ Car Interest Agent успешно завершил работу через tools")
        else:
            logger.warning("⚠️ Car Interest Agent не подтвердил завершение")
            all_confirmed = False
    
    if all_confirmed:
        logger.info("\n🎉 ВСЕ АГЕНТЫ РАБОТАЮТ КОРРЕКТНО С TOOL CALLING!")
    else:
        logger.warning("\n⚠️ Некоторые агенты не завершили работу корректно")