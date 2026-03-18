"""Notification Celery tasks — stubs for Phase 1. Implemented in Phase 5."""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_weekly_recommendations")
def send_weekly_recommendations(self):
    """Weekly: Send recommendation emails. Implemented Phase 5."""
    return {"status": "stub — implement in Phase 5"}
