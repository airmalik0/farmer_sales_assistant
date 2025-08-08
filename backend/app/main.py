from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
import atexit
from .core.database import engine, SessionLocal
from .models import Client, Message, MessageAttachment, Dossier, CarInterest, Task, Settings, Trigger, TriggerLog
from .api import api_router
from .services.trigger_service import TriggerService
from .services.task_service import TaskService
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

# Настройка логирования для планировщика
scheduler_logger = logging.getLogger("scheduler")
scheduler_logger.setLevel(logging.INFO)

# Глобальный планировщик
scheduler = AsyncIOScheduler()

async def run_trigger_check():
    """Функция для автоматической проверки триггеров"""
    scheduler_logger.info("Запуск автоматической проверки триггеров...")
    
    db = SessionLocal()
    try:
        result = await TriggerService.check_all_triggers(db)
        scheduler_logger.info(f"Проверка триггеров завершена: {result.get('message', 'OK')}")
    except Exception as e:
        scheduler_logger.error(f"Ошибка при проверке триггеров: {e}")
    finally:
        db.close()

async def run_task_reminders():
    """Функция для автоматической отправки напоминаний о просроченных задачах"""
    scheduler_logger.info("Запуск автоматической отправки напоминаний о задачах...")
    
    db = SessionLocal()
    try:
        sent_count = await TaskService.send_overdue_reminders(db)
        scheduler_logger.info(f"Отправка напоминаний завершена: отправлено {sent_count} напоминаний")
        return {"sent_count": sent_count, "message": f"Отправлено {sent_count} напоминаний о просроченных задачах"}
    except Exception as e:
        scheduler_logger.error(f"Ошибка при отправке напоминаний о задачах: {e}")
        return {"sent_count": 0, "message": f"Ошибка: {e}"}
    finally:
        db.close()

async def run_daily_tasks_summary():
    """Функция для автоматической отправки ежедневной сводки задач"""
    scheduler_logger.info("Запуск автоматической отправки ежедневной сводки задач...")
    
    db = SessionLocal()
    try:
        from .services.telegram_admin_service import TelegramAdminService
        # Временно отключаем ежедневную сводку пока не реализуем её через админ сервис
        message = "Ежедневная сводка задач временно отключена (переход на Pact API)"
        scheduler_logger.info(message)
        return {"success": True, "message": message}
    except Exception as e:
        scheduler_logger.error(f"Ошибка при отправке ежедневной сводки задач: {e}")
        return {"success": False, "message": f"Ошибка: {e}"}
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    scheduler_logger.info("Запуск планировщика...")
    
    # Добавляем задачу проверки триггеров каждые 5 минут
    scheduler.add_job(
        run_trigger_check,
        trigger=IntervalTrigger(minutes=5),
        id='trigger_check',
        name='Проверка триггеров каждые 5 минут',
        replace_existing=True,
        max_instances=1  # Предотвращаем параллельное выполнение
    )
    
    # Добавляем задачу отправки напоминаний о задачах каждые 5 минут
    scheduler.add_job(
        run_task_reminders,
        trigger=IntervalTrigger(minutes=5),
        id='task_reminders',
        name='Напоминания о задачах каждые 5 минут',
        replace_existing=True,
        max_instances=1
    )
    
    # Добавляем задачу отправки ежедневной сводки задач каждый день в 8:00
    scheduler.add_job(
        run_daily_tasks_summary,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_tasks_summary',
        name='Ежедневная сводка задач каждый день в 8:00',
        replace_existing=True,
        max_instances=1
    )
    
    # Запускаем планировщик
    scheduler.start()
    scheduler_logger.info("Планировщик запущен. Проверка триггеров каждые 5 минут, напоминания о задачах каждые 5 минут, ежедневная сводка в 8:00.")
    
    # Запускаем первую проверку сразу (опционально)
    try:
        await run_trigger_check()
        scheduler_logger.info("Первая проверка триггеров выполнена при старте приложения")
    except Exception as e:
        scheduler_logger.error(f"Ошибка при первой проверке триггеров: {e}")
    
    # Регистрируем обработчик для корректного завершения
    atexit.register(lambda: scheduler.shutdown())
    
    yield
    
    # Shutdown
    scheduler_logger.info("Остановка планировщика...")
    scheduler.shutdown()

# Создание таблиц теперь происходит через Alembic миграции
# Запустите: alembic upgrade head

app = FastAPI(
    title="Farmer CRM API",
    description="API для CRM-системы Фермер",
    version="1.0.0",
    lifespan=lifespan
)

# Проброс заголовков от reverse proxy (https scheme, real ip)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production нужно будет ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Farmer CRM API v1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/scheduler/status")
async def scheduler_status():
    """Получить статус планировщика"""
    jobs = scheduler.get_jobs()
    return {
        "running": scheduler.running,
        "jobs_count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    }


@app.post("/scheduler/trigger-check/run")
async def manual_trigger_check():
    """Запустить проверку триггеров вручную"""
    try:
        await run_trigger_check()
        return {
            "success": True,
            "message": "Проверка триггеров запущена вручную"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при ручном запуске проверки триггеров: {e}"
        }

@app.post("/scheduler/task-reminders/run")
async def manual_task_reminders():
    """Запустить отправку напоминаний о задачах вручную"""
    try:
        result = await run_task_reminders()
        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при ручном запуске напоминаний о задачах: {e}"
        }

@app.post("/scheduler/daily-summary/run")
async def manual_daily_summary():
    """Запустить отправку ежедневной сводки задач вручную"""
    try:
        result = await run_daily_tasks_summary()
        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при ручном запуске ежедневной сводки задач: {e}"
        }