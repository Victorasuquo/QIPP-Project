from beanie import Document
from typing import Optional, Dict, Any
from datetime import datetime


class PracticeMeasureDocument(Document):
    practice_ods_code: str
    measure_id: Optional[str] = None
    measure_name: Optional[str] = None
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    calc_value: Optional[float] = None
    percentile: Optional[float] = None
    actual_cost: Optional[float] = None
    date: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    fetched_at: Optional[datetime] = None

    class Settings:
        name = "practice_measures"
        indexes = ["practice_ods_code", "measure_id", "date"]
