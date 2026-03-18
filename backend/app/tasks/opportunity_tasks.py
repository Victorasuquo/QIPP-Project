"""Opportunity discovery Celery tasks — stubs for Phase 1. Victor implements in Phase 5."""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.opportunity_tasks.discover_opportunities")
def discover_opportunities(self, sub_icb_ods: str = "02P"):
    """Daily: Run Victor's OpportunityDiscoveryEngine for South Yorkshire. Implemented Phase 5."""
    return {"status": "stub — implement in Phase 5"}
