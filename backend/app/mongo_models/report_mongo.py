from beanie import Document
from typing import Optional, Dict, Any
from datetime import datetime


class ICBReportDocument(Document):
    icb_ods: str
    report_period: str  # e.g. "2026-03"
    report_type: str = "monthly"
    data: Optional[Dict[str, Any]] = None
    generated_at: Optional[datetime] = None

    class Settings:
        name = "icb_monthly_reports"
        indexes = ["icb_ods", "report_period"]
