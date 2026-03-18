from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class ActionSheetRequest(BaseModel):
    opportunity_title: str = Field(..., min_length=3, max_length=300)
    practice_name: str = Field(..., min_length=2, max_length=200)
    patient_count: int = Field(default=0, ge=0)
    current_drug: Optional[str] = None
    target_drug: Optional[str] = None
    clinical_notes: Optional[str] = None


class PatientLetterRequest(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=200)
    opportunity_title: str = Field(..., min_length=3, max_length=300)
    current_drug: str = Field(..., min_length=2, max_length=200)
    target_drug: str = Field(..., min_length=2, max_length=200)
    practice_name: str = Field(..., min_length=2, max_length=200)
    additional_advice: Optional[str] = None


class SMSRequest(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=120)
    practice_name: str = Field(..., min_length=2, max_length=200)
    current_drug: str = Field(..., min_length=2, max_length=200)
    target_drug: str = Field(..., min_length=2, max_length=200)


class GeneratedDocumentResponse(BaseModel):
    document_id: uuid.UUID
    document_type: str
    title: str
    content: str
    generated_at: datetime


class StoredDocumentResponse(GeneratedDocumentResponse):
    generated_by_user_id: Optional[uuid.UUID] = None
    tenant_id: Optional[uuid.UUID] = None


class SendEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str = Field(..., min_length=3, max_length=250)
    body: str = Field(..., min_length=5, max_length=12000)
    category: str = Field(default="recommendation", max_length=50)
