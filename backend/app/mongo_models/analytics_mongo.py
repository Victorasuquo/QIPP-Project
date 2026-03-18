from beanie import Document
from typing import Optional, Dict


class PatientAnalyticsDocument(Document):
    patient_nhs_number: Optional[str] = None
    current_annual_cost: float = 0.0
    alternative_annual_cost: float = 0.0
    potential_savings: float = 0.0
    risk_score: float = 0.0
    eligibility_checks: Dict[str, bool] = {}

    class Settings:
        name = "patient_analytics"
        indexes = ["patient_nhs_number"]
