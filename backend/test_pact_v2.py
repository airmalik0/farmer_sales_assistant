#!/usr/bin/env python
"""Тест миграции на Pact API V2"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем путь к модулю
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
load_dotenv()

from app.services.pact_service import PactService
from app.core.config import settings

async def test_raw_api():
    """Тест прямого вызова API"""
    import httpx
    
    print("\n4. Тест прямого вызова API:")
    
    # Сначала попробуем получить информацию о компании
    url_companies = f"https://api.pact.im/p1/companies/{settings.pact_company_id}"
    headers = {
        "X-Private-Api-Token": settings.pact_api_token
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_companies, headers=headers)
            print(f"   Company info status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Company name: {data.get('data', {}).get('name', 'N/A')}")
    except Exception as e:
        print(f"   Company API error: {e}")
    
    # Теперь пробуем получить беседы
    url_conversations = f"https://api.pact.im/p1/companies/{settings.pact_company_id}/conversations"
    params = {
        "page": 1,
        "per": 5,
        "sort_direction": "desc"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_conversations, headers=headers, params=params)
            print(f"   Conversations API status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total conversations: {data.get('meta', {}).get('total', 0)}")
                if data.get('data'):
                    print(f"   First conversation ID: {data['data'][0].get('id')}")
    except Exception as e:
        print(f"   V2 API error: {e}")

async def test_pact_v2():
    """Тестирование методов Pact API"""
    
    print("=" * 50)
    print("ТЕСТ PACT API")
    print("=" * 50)
    
    # Проверяем настройки
    print("\n1. Проверка настроек:")
    print(f"   API Token: {'✓' if settings.pact_api_token else '✗ Отсутствует'}")
    print(f"   Company ID: {settings.pact_company_id if settings.pact_company_id else '✗ Не указан'}")
    print(f"   Base URL: {PactService.BASE_URL}")
    
    if not settings.pact_api_token:
        print("\n❌ ОШИБКА: Не настроен PACT_API_TOKEN в .env")
        return
    
    if not settings.pact_company_id:
        print("\n❌ ОШИБКА: Не настроен PACT_COMPANY_ID в .env")
        return
    
    # Тест получения бесед
    print("\n2. Тест получения бесед:")
    try:
        conversations = await PactService.get_conversations(page=1, per_page=5)
        if conversations:
            print(f"   ✓ Получено бесед: {len(conversations.get('data', []))}")
            print(f"   Всего бесед: {conversations.get('meta', {}).get('total', 0)}")
            if conversations.get('data'):
                first = conversations['data'][0]
                print(f"   Пример беседы:")
                print(f"     - ID: {first.get('id')}")
                print(f"     - Channel: {first.get('channel', {}).get('type')}")
                print(f"     - Name: {first.get('name')}")
        else:
            print("   ✗ Не удалось получить беседы")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
    
    # Тест получения сообщений (если есть беседы)
    print("\n3. Тест получения сообщений беседы:")
    try:
        conversations = await PactService.get_conversations(page=1, per_page=1)
        if conversations and conversations.get('data'):
            conv_id = conversations['data'][0]['id']
            messages = await PactService.get_conversation_messages(conv_id, page=1, per_page=5)
            if messages:
                print(f"   ✓ Получено сообщений: {len(messages.get('data', []))}")
                if messages.get('data') and len(messages['data']) > 0:
                    print(f"   Последнее сообщение от: {messages['data'][0].get('from')}")
            else:
                print("   ✗ Не удалось получить сообщения")
        else:
            print("   ⚠ Нет бесед для теста")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print("Тест Pact API завершен!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_pact_v2())
    asyncio.run(test_raw_api())