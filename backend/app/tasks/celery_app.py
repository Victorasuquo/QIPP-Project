from celery import Celery
from app.config import settings

celery_app = Celery(
    "qipp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.data_sync",
        "app.tasks.opportunity_tasks",
        "app.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/London",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "daily-tariff-sync": {
            "task": "app.tasks.data_sync.sync_tariff_prices",
            "schedule": 60 * 60 * 24,  # daily
            "options": {"queue": "data_sync"},
        },
        "daily-opportunity-discovery": {
            "task": "app.tasks.opportunity_tasks.discover_opportunities",
            "schedule": 60 * 60 * 24,  # daily
            "options": {"queue": "discovery"},
        },
        "weekly-recommendations": {
            "task": "app.tasks.notification_tasks.send_weekly_recommendations",
            "schedule": 60 * 60 * 24 * 7,  # weekly
            "options": {"queue": "notifications"},
        },
    },
)
