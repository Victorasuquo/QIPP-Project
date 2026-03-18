from pydantic import BaseModel
from typing import Optional, List
import uuid


class WorkstreamSummary(BaseModel):
    workstream: str
    total_savings: float
    opportunity_count: int
    patients_affected: int
    top_opportunity_description: Optional[str] = None


class DashboardSummary(BaseModel):
    total_saving_potential: float
    active_opportunities: int
    total_practices: int
    completed_switches: int
    realized_savings_ytd: float
    workstream_breakdown: List[WorkstreamSummary]
    data_as_of: Optional[str] = None


class OpportunityResponse(BaseModel):
    id: str
    workstream: str
    description: str
    estimated_annual_savings: float
    patients_affected: int
    status: str
    org_level: str
    practice_ods_code: Optional[str] = None
    pcn_ods_code: Optional[str] = None
    sub_icb_ods_code: Optional[str] = None
    therapeutic_area: Optional[str] = None
    effort_reward_score: Optional[float] = None
    priority_rank: Optional[int] = None
    current_expensive_bnf: Optional[str] = None
    target_cheap_bnf: Optional[str] = None


class OpportunityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[OpportunityResponse]


class InterventionResponse(BaseModel):
    id: uuid.UUID
    name: str
    therapeutic_area: Optional[str] = None
    workstream_code: Optional[str] = None
    current_drug: str
    target_drug: str
    status: str
    forecast_annual_savings: Optional[float] = None
    realized_savings: float
    total_eligible_patients: int
    patients_switched: int

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    category: str
    is_read: bool

    model_config = {"from_attributes": True}


class ICBResponse(BaseModel):
    id: uuid.UUID
    name: str
    ods_code: str
    postcode: Optional[str] = None
    email_domain: Optional[str] = None

    model_config = {"from_attributes": True}


class PCNResponse(BaseModel):
    id: uuid.UUID
    name: str
    ods_code: str
    sub_icb_ods_code: Optional[str] = None
    postcode: Optional[str] = None

    model_config = {"from_attributes": True}


class PracticeResponse(BaseModel):
    id: uuid.UUID
    name: str
    ods_code: str
    sub_icb_ods_code: Optional[str] = None
    postcode: Optional[str] = None

    model_config = {"from_attributes": True}


class SavingsPoint(BaseModel):
    period: str
    amount: float


class SavingsSummary(BaseModel):
    ytd_total: float
    monthly_trend: List[SavingsPoint]
    by_workstream: dict
