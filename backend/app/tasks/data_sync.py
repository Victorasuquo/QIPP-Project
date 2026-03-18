"""Data sync Celery tasks — stubs for Phase 1. Implementations added in Phase 5."""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.data_sync.sync_tariff_prices")
def sync_tariff_prices(self):
    """Daily: Download Drug Tariff from OpenPrescribing → MongoDB. Implemented Phase 5."""
    return {"status": "stub — implement in Phase 5"}
