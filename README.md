# 🌾 Фермер CRM - Система продаж с Telegram-ботом

> Полнофункциональная CRM-система для ведения продаж через Telegram с AI-анализом клиентов

## 🚀 Быстрый старт

```bash
# 1. Клонируйте проект
git clone <repository-url>
cd farmer-crm

# 2. Настройте переменные окружения
cp .env.example .env
# Заполните .env файл (см. инструкцию ниже)

# 3. Запустите все сервисы
docker-compose up -d

# 4. Откройте панель управления
open http://localhost:3000
```

## 📋 Основные функции

### ✅ MVP Функционал
- 🤖 **Telegram-бот** для клиентов
- 💻 **Веб-панель** для менеджера (без авторизации)
- 💬 **Двустороннее общение** через единый интерфейс
- 📢 **Массовые рассылки** с персонализацией
- 🤖 **AI-досье клиентов** (автоматически через 5 минут)
- ⚡ **Real-time обновления** через WebSocket

### 🎯 Критерии приемки
- [x] Административная панель доступна по прямой ссылке
- [x] Новые клиенты автоматически появляются в списке
- [x] Двусторонняя переписка работает
- [x] Массовая рассылка запускается от фермера
- [x] AI создает досье через 5 минут после диалога
- [x] Данные корректно сохраняются в PostgreSQL

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   Web Dashboard │    │   PostgreSQL    │
│   (aiogram)     │◄──►│   (React/TS)    │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FastAPI Backend│    │   WebSocket     │    │     Redis       │
│   (Python)      │◄──►│   Real-time     │◄──►│   (Celery)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   OpenAI API    │
│   (AI Dossier)  │
└─────────────────┘
```

## 🔧 Технологический стек

| Компонент | Технология |
|-----------|------------|
| **Backend** | FastAPI, SQLAlchemy, PostgreSQL |
| **Frontend** | React, TypeScript, Vite, Tailwind CSS |
| **Bot** | aiogram (Python) |
| **AI** | OpenAI GPT-3.5-turbo |
| **Tasks** | Celery + Redis |
| **Real-time** | WebSockets |
| **Containerization** | Docker, Docker Compose |

## ⚙️ Настройка

### 1. Telegram Bot
```bash
# 1. Создайте бота через @BotFather
# 2. Получите токен
# 3. Узнайте свой Telegram ID через @userinfobot
```

### 2. OpenAI API
```bash
# 1. Зарегистрируйтесь на platform.openai.com
# 2. Создайте API ключ
# 3. Добавьте его в .env файл
```

### 3. Переменные окружения (.env)
```env
# Database
DATABASE_URL=postgresql://farmer:password@localhost:5432/farmer_crm

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
FARMER_TELEGRAM_ID=123456789

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Redis  
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your_secret_key_here
```

## 🎮 Использование

### Для менеджера:
1. 🌐 Откройте http://localhost:3000
2. 👥 Выберите клиента из списка слева
3. 💬 Ведите переписку в центральном окне
4. 📊 Изучайте AI-досье справа
5. 📢 Для рассылки - напишите боту с вашего аккаунта

### Для клиентов:
1. 🔍 Найдите бота в Telegram
2. ▶️ Отправьте `/start`
3. 💭 Общайтесь как обычно

## 📁 Структура проекта

```
farmer-crm/
├── 🔧 backend/           # FastAPI API
│   ├── app/
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── schemas/      # Pydantic схемы  
│   │   ├── api/          # REST API
│   │   ├── services/     # Бизнес-логика
│   │   └── core/         # Конфигурация
│   └── alembic/          # Миграции БД
├── 🎨 frontend/          # React Dashboard
│   ├── src/
│   │   ├── components/   # React компоненты
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API клиенты
│   │   └── types/        # TypeScript типы
├── 🤖 bot/              # Telegram Bot
│   ├── handlers/         # Обработчики сообщений
│   └── services/         # Интеграция с API
└── 🐳 docker-compose.yml # Оркестрация
```

## 📚 Документация

- 📖 **[Полная инструкция по установке](./SETUP.md)**
- 🔗 **[API документация](http://localhost:8000/docs)** (после запуска)
- 🏗️ **[Техническое задание](./docs/requirements.md)**

## 🚀 Доступные сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| 🖥️ **Dashboard** | http://localhost:3000 | Веб-панель менеджера |
| 🔗 **API** | http://localhost:8000 | REST API + документация |
| 🗄️ **PostgreSQL** | localhost:5432 | База данных |
| 🔴 **Redis** | localhost:6379 | Кеш + очереди задач |

## 🐛 Отладка

```bash
# Просмотр логов
docker-compose logs -f

# Перезапуск сервиса  
docker-compose restart backend

# Подключение к БД
docker-compose exec postgres psql -U farmer -d farmer_crm
```

## 📈 Планы развития

- [ ] Авторизация и роли пользователей
- [ ] Аналитика и отчеты
- [ ] Интеграция с CRM системами
- [ ] Мобильное приложение
- [ ] Расширенные AI функции

---

**Статус**: ✅ MVP готов к использованию  
**Версия**: 1.0.0  
**Лицензия**: MIT