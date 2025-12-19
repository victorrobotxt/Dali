import os
from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "glashaus_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Sofia",
    enable_utc=True,
)

# Auto-discover tasks in src/tasks.py
celery_app.autodiscover_tasks(['src.tasks'])
