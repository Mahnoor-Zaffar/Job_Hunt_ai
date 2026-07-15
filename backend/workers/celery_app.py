from celery import Celery
from celery.schedules import crontab

from backend.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "job_hunting",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "run-all-scrapers": {
        "task": "run_all_scrapers",
        "schedule": crontab(minute=f"*/{settings.SCRAPE_INTERVAL_MINUTES}"),
        "options": {
            "expires": settings.SCRAPE_INTERVAL_MINUTES * 60 - 10,
        },
    },
}

celery_app.autodiscover_tasks(["backend.workers.tasks"])
