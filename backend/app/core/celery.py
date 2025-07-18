from celery import Celery
from .config import settings

celery_app = Celery(
    "farmer_crm",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.services.ai_service"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)