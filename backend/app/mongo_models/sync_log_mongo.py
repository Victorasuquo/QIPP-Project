from beanie import Document
from typing import Optional
from datetime import datetime


class SyncLogDocument(Document):
    run_id: Optional[str] = None
    trigger: Optional[str] = None
    status: str = "pending"
    patients_fetched: int = 0
    patients_created: int = 0
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None

    class Settings:
        name = "sync_logs"


class MedSyncLogDocument(Document):
    run_id: Optional[str] = None
    status: str = "pending"
    records_synced: int = 0
    workstream: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None

    class Settings:
        name = "med_sync_logs"


class TariffSyncLogDocument(Document):
    run_id: Optional[str] = None
    status: str = "pending"
    records_inserted: int = 0
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None

    class Settings:
        name = "tariff_sync_logs"
