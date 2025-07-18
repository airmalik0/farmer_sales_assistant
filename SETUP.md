# Инструкция по установке и запуску проекта "Фермер CRM"

## Описание

CRM-система "Фермер" состоит из:
- **Backend**: FastAPI с PostgreSQL и Redis
- **Frontend**: React с TypeScript и Tailwind CSS
- **Bot**: Telegram бот на aiogram
- **AI**: Интеграция с OpenAI для автоматического создания досье клиентов
- **Workers**: Celery для фоновых задач

## Предварительные требования

- Docker и Docker Compose
- Git

## Установка

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository-url>
   cd farmer-crm
   ```

2. **Создайте файл переменных окружения**
   ```bash
   cp .env.example .env
   ```

3. **Заполните переменные окружения в `.env`**
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

   # Backend
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8000

   # Frontend
   FRONTEND_PORT=3000

   # Security
   SECRET_KEY=your_secret_key_here
   ```

## Настройка Telegram бота

1. **Создайте бота в Telegram**
   - Напишите @BotFather в Telegram
   - Отправьте команду `/newbot`
   - Следуйте инструкциям для создания бота
   - Скопируйте токен бота в `TELEGRAM_BOT_TOKEN`

2. **Получите ваш Telegram ID**
   - Напишите @userinfobot в Telegram
   - Отправьте любое сообщение
   - Скопируйте ваш ID в `FARMER_TELEGRAM_ID`

## Настройка OpenAI

1. **Получите API ключ OpenAI**
   - Зарегистрируйтесь на https://platform.openai.com
   - Создайте API ключ в разделе API Keys
   - Скопируйте ключ в `OPENAI_API_KEY`

## Запуск проекта

1. **Запустите все сервисы через Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Проверьте статус сервисов**
   ```bash
   docker-compose ps
   ```

3. **Создайте миграции базы данных (первый запуск)**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

## Доступ к сервисам

- **Frontend (Dashboard)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Использование

### Для фермера (менеджера):

1. **Доступ к панели**
   - Откройте http://localhost:3000 в браузере
   - Панель доступна без авторизации (MVP)

2. **Работа с клиентами**
   - Клиенты появляются автоматически при написании в бота
   - Выберите клиента из списка слева
   - Ведите переписку в центральном окне
   - Просматривайте досье клиента справа

3. **Массовые рассылки**
   - Напишите любое сообщение боту с вашего аккаунта (FARMER_TELEGRAM_ID)
   - Бот автоматически разошлет его всем клиентам с персональным приветствием

### Для клиентов:

1. **Начало работы**
   - Найдите вашего бота в Telegram по имени
   - Отправьте команду `/start`
   - Начните общение с ботом

2. **Общение**
   - Отправляйте текстовые сообщения
   - Поддерживаются голосовые сообщения, фото, документы
   - Все сообщения сохраняются и отображаются в панели менеджера

## Функции системы

### ✅ Реализованные функции

- Telegram бот для клиентов
- Веб-панель для менеджера
- Двустороннее общение через панель
- Массовые рассылки
- Автоматическое создание клиентов
- AI анализ диалогов и создание досье
- Real-time обновления через WebSocket
- Поддержка разных типов сообщений

### 🔄 AI Досье

- Автоматически создается через 5 минут после завершения диалога
- Анализирует стиль общения, потребности, этап в воронке
- Обновляется при новых диалогах
- Помогает менеджеру лучше понимать клиента

### 📊 Архитектура

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
│   (AI Dosier)   │
└─────────────────┘
```

## Отладка

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f bot
docker-compose logs -f frontend
```

### Перезапуск сервисов

```bash
# Перезапуск всех сервисов
docker-compose restart

# Перезапуск конкретного сервиса
docker-compose restart backend
```

### Подключение к базе данных

```bash
docker-compose exec postgres psql -U farmer -d farmer_crm
```

## Разработка

### Добавление новых зависимостей

**Backend:**
```bash
# Добавить в backend/requirements.txt
docker-compose exec backend pip install package_name
docker-compose restart backend
```

**Frontend:**
```bash
# Войти в контейнер
docker-compose exec frontend sh
npm install package_name
```

### Создание миграций

```bash
docker-compose exec backend alembic revision --autogenerate -m "Description"
docker-compose exec backend alembic upgrade head
```

## Производственное развертывание

1. Измените пароли и ключи в `.env`
2. Настройте reverse proxy (nginx)
3. Используйте внешние PostgreSQL и Redis
4. Настройте SSL сертификаты
5. Настройте мониторинг и логирование

## Поддержка

При возникновении проблем проверьте:
1. Корректность переменных окружения
2. Доступность внешних сервисов (Telegram API, OpenAI API)
3. Логи сервисов
4. Статус Docker контейнеров