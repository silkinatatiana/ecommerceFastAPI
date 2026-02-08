from celery import Celery
from celery.schedules import crontab

from config import Config


celery_app = Celery(
    "ecommerce_app",
    broker=Config.BROKER_URL,
    backend=Config.BROKER_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "compute-recommendations-every-2-min": {
        "task": "generate_recommendations",
        "schedule": crontab(minute=Config.SCHEDULE_REC_MIN),
    },
}
