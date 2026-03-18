from pydantic import BaseModel, Field
from typing import Optional


class ClinicalQueryRequest(BaseModel):
    query_text: str = Field(..., min_length=5, max_length=4000)
    target_system: Optional[str] = Field(default="both", description="emis | systmone | both")


class ClinicalQueryResponse(BaseModel):
    query_text: str
    target_system: str
    emis_query: str
    systmone_query: str
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]
    safety_notes: list[str]


class FindOpportunitiesRequest(BaseModel):
    query_text: str = Field(..., min_length=5, max_length=4000)
    max_results: int = Field(default=5, ge=1, le=20)


class OpportunityIdea(BaseModel):
    title: str
    rationale: str
    current_drug: Optional[str] = None
    target_drug: Optional[str] = None
    estimated_annual_savings: float = 0.0
    affected_patients: int = 0
    bnf_codes: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    evidence_summary: Optional[str] = None
    confidence_score: Optional[float] = None
    citations: list[str] = Field(default_factory=list)


class FindOpportunitiesResponse(BaseModel):
    query_text: str
    opportunities: list[OpportunityIdea]
