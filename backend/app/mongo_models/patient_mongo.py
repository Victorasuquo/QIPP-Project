from beanie import Document
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MedicationItem(BaseModel):
    bnf_code: Optional[str] = None
    name: Optional[str] = None
    dose: Optional[str] = None
    is_current: bool = True
    cost_per_unit: Optional[float] = None


class ConditionItem(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None


class PatientDocument(Document):
    nhs_number: Optional[str] = None
    practice_ods_code: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    renal_function_egfr: Optional[int] = None
    hba1c: Optional[float] = None
    systolic_bp: Optional[int] = None
    weight_kg: Optional[float] = None
    smoking_status: Optional[str] = None
    diabetes_type: Optional[str] = None
    medications: List[MedicationItem] = []
    conditions: List[ConditionItem] = []
    contraindications: List[str] = []
    risk_level: Optional[str] = "low"
    risk_score: Optional[float] = None
    is_switch_eligible: bool = False
    estimated_annual_savings: Optional[float] = None
    workstream: Optional[str] = None
    eligibility_reasons: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Settings:
        name = "patients"
        indexes = ["nhs_number", "practice_ods_code", "workstream", "is_switch_eligible"]


class PrescriptionDocument(Document):
    patient_id: Optional[str] = None
    nhs_number: Optional[str] = None
    bnf_code: Optional[str] = None
    drug_name: Optional[str] = None
    quantity: Optional[float] = None
    items: Optional[int] = None
    actual_cost: Optional[float] = None
    prescribed_date: Optional[datetime] = None
    practice_ods_code: Optional[str] = None

    class Settings:
        name = "prescriptions"
