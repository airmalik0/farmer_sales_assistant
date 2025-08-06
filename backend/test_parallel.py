"""Тест параллельной обработки агентов"""

import os
import time
import logging
from datetime import datetime

# Настройка LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "farmer-crm-parallel-test"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

print("\n" + "="*50)
print("🚀 Тест ПАРАЛЛЕЛЬНОЙ обработки агентов")
print("="*50 + "\n")

from app.models.message import Message, SenderType
from app.services.ai.parallel_analyzer import parallel_analyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_messages():
    """Создает тестовые сообщения"""
    return [
        Message(
            client_id=1,
            sender=SenderType.client,
            content="Привет! Я Петр из Санкт-Петербурга. Ищу Mercedes GLE 2023, бюджет 100-120к$. Мой день рождения 25 декабря.",
            content_type="text",
            income=True,
            timestamp=datetime.now()
        ),
        Message(
            client_id=1,
            sender=SenderType.farmer,
            content="Здравствуйте, Петр! Отличный выбор! Давайте встретимся завтра в 14:00 для обсуждения?",
            content_type="text",
            income=False,
            timestamp=datetime.now()
        ),
        Message(
            client_id=1,
            sender=SenderType.client,
            content="Да, завтра в 14:00 подходит. Интересует черный или серый цвет, полный привод обязательно.",
            content_type="text",
            income=True,
            timestamp=datetime.now()
        )
    ]


def test_sequential():
    """Тест последовательной обработки"""
    logger.info("Запуск ПОСЛЕДОВАТЕЛЬНОЙ обработки...")
    messages = create_test_messages()
    
    start_time = time.time()
    
    # Импортируем агентов
    from app.services.ai.task_agent import task_agent
    from app.services.ai.dossier_agent import dossier_agent
    from app.services.ai.car_interest_agent import car_interest_agent
    
    # Запускаем последовательно
    task_result = task_agent.analyze(1, "Петр", messages)
    dossier_result = dossier_agent.analyze(1, "Петр", messages)
    car_result = car_interest_agent.analyze(1, "Петр", messages)
    
    sequential_time = time.time() - start_time
    
    return sequential_time, {
        "task": task_result,
        "dossier": dossier_result,
        "car_interest": car_result
    }


def test_parallel():
    """Тест параллельной обработки"""
    logger.info("Запуск ПАРАЛЛЕЛЬНОЙ обработки...")
    messages = create_test_messages()
    
    start_time = time.time()
    
    # Запускаем параллельно
    result = parallel_analyzer.analyze_all(
        client_id=1,
        client_name="Петр",
        chat_messages=messages
    )
    
    parallel_time = time.time() - start_time
    
    return parallel_time, result


if __name__ == "__main__":
    print("📝 Тестовый сценарий: клиент Петр ищет Mercedes GLE\n")
    
    # Последовательная обработка
    print("1️⃣ ПОСЛЕДОВАТЕЛЬНАЯ обработка:")
    seq_time, seq_results = test_sequential()
    print(f"   ⏱️ Время: {seq_time:.2f} секунд")
    print(f"   ✅ Task: {seq_results['task'].get('confirmed', False)}")
    print(f"   ✅ Dossier: {seq_results['dossier'].get('confirmed', False)}")
    print(f"   ✅ Car Interest: {seq_results['car_interest'].get('confirmed', False)}")
    
    print("\n2️⃣ ПАРАЛЛЕЛЬНАЯ обработка:")
    par_time, par_results = test_parallel()
    print(f"   ⏱️ Время: {par_time:.2f} секунд")
    print(f"   ✅ All confirmed: {par_results['all_confirmed']}")
    
    # Сравнение
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ:")
    print(f"   Последовательно: {seq_time:.2f}с")
    print(f"   Параллельно: {par_time:.2f}с")
    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"   🚀 Ускорение: {speedup:.1f}x")
    print(f"   ⏱️ Экономия времени: {seq_time - par_time:.2f} секунд")
    
    if par_results['errors']:
        print(f"\n⚠️ Ошибки при параллельной обработке:")
        for agent, error in par_results['errors'].items():
            print(f"   - {agent}: {error}")
    
    print("="*50)