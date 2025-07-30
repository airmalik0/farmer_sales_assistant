from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import Base
from app.models import Client, Message, Dossier

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    # Сначала проверяем переменную окружения
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Если переменная не установлена, пытаемся определить окружение
    # Проверяем, работаем ли мы локально (есть ли локальный PostgreSQL)
    try:
        import psycopg2
        # Пытаемся подключиться с локальными креденциалами
        test_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="farmer_crm"
        )
        test_conn.close()
        print("🔍 Обнаружено локальное окружение, использую postgres:postgres")
        return "postgresql://postgres:postgres@localhost:5432/farmer_crm"
    except:
        # Если не удалось подключиться с postgres:postgres, используем farmer
        print("🐳 Используем настройки Docker (farmer:password)")
        return "postgresql://farmer:password@localhost:5432/farmer_crm"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()