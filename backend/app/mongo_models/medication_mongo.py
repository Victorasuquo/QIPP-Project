from beanie import Document
from typing import Optional
from datetime import datetime


class MedicationDocument(Document):
    bnf_code: str
    name: str
    bnf_chapter: Optional[str] = None
    bnf_section: Optional[str] = None
    is_generic: bool = False
    cost_per_unit: Optional[float] = None
    workstream: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Settings:
        name = "medications"
        indexes = ["bnf_code", "workstream", "is_generic"]
