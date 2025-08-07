# Alembic migrations setup

После клонирования проекта на сервере нужно создать папку для миграций и выполнить начальную миграцию:

```bash
# Создать папку для миграций
mkdir -p backend/alembic/versions

# Запустить контейнеры
docker-compose up -d

# Сгенерировать начальную миграцию
docker exec farmer_sales_assistant-backend-1 alembic revision --autogenerate -m "Initial migration"

# Применить миграцию
docker exec farmer_sales_assistant-backend-1 alembic upgrade head
```

Папка `backend/alembic/versions/` добавлена в .gitignore и не отслеживается git.
Миграции нужно генерировать локально на каждой среде.
