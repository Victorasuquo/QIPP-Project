from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional


class OpportunityDocument(Document):
    opportunity_id: Optional[str] = None
    org_level: str = "sub_icb"
    practice_ods_code: Optional[str] = None
    pcn_ods_code: Optional[str] = None
    sub_icb_ods_code: Optional[str] = None
    icb_id: Optional[str] = None
    workstream: str
    description: str = ""
    estimated_annual_savings: float = 0.0
    patients_affected: int = 0
    effort_reward_score: float = 0.0
    current_expensive_bnf: Optional[str] = None
    target_cheap_bnf: Optional[str] = None
    status: str = "IDENTIFIED"
    priority_rank: Optional[int] = None
    therapeutic_area: Optional[str] = None
    spending_data_fetched: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Settings:
        name = "opportunities"
        indexes = [
            "org_level",
            "practice_ods_code",
            "pcn_ods_code",
            "sub_icb_ods_code",
            "icb_id",
            "workstream",
            "status",
        ]
