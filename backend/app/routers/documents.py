from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.ai import AIDecisionAudit
from app.schemas.documents import (
    ActionSheetRequest,
    PatientLetterRequest,
    SMSRequest,
    GeneratedDocumentResponse,
    StoredDocumentResponse,
)
from app.services.gemini_service import GeminiService, GeminiServiceError

router = APIRouter(prefix="/documents", tags=["Documents"])


def _fallback_action_sheet(body: ActionSheetRequest) -> str:
    return (
        f"Practice Action Sheet\n"
        f"Opportunity: {body.opportunity_title}\n"
        f"Practice: {body.practice_name}\n"
        f"Estimated patients: {body.patient_count}\n\n"
        "1) Validate patient cohort in EMIS/SystmOne.\n"
        "2) Apply exclusion criteria and pharmacist review.\n"
        "3) Approve switch and contact eligible patients.\n"
        "4) Issue updated prescriptions and record outcomes.\n"
        "5) Track realized savings monthly.\n"
    )


def _fallback_patient_letter(body: PatientLetterRequest) -> str:
    return (
        f"Dear {body.patient_name},\n\n"
        f"Your GP practice ({body.practice_name}) is reviewing repeat medicines as part of routine NHS care. "
        f"We are considering a switch from {body.current_drug} to {body.target_drug} for your treatment plan.\n\n"
        "This change is designed to provide the same clinical benefit while supporting safe and cost-effective prescribing. "
        "A clinician will review your record before any change is made.\n\n"
        "If you have concerns, please contact the practice team.\n\n"
        "Kind regards,\n"
        "Medicines Optimisation Team"
    )


def _fallback_sms(body: SMSRequest) -> str:
    sms = (
        f"{body.practice_name}: We are reviewing your repeat medication and may switch "
        f"{body.current_drug} to {body.target_drug}. Please contact us with concerns."
    )
    return sms[:160]


async def _store_document(
    db: AsyncSession,
    current_user,
    document_type: str,
    title: str,
    content: str,
    source_payload: dict,
) -> GeneratedDocumentResponse:
    record = AIDecisionAudit(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=f"generate_{document_type}",
        input_summary=title,
        output_summary=content,
        guardrail_safe=True,
        endpoint=f"/api/documents/{document_type}",
        extra={
            "document_type": document_type,
            "title": title,
            "content": content,
            "source_payload": source_payload,
        },
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return GeneratedDocumentResponse(
        document_id=record.id,
        document_type=document_type,
        title=title,
        content=content,
        generated_at=record.created_at,
    )


@router.post("/action-sheet", response_model=GeneratedDocumentResponse)
async def generate_action_sheet(
    body: ActionSheetRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    title = f"Action Sheet: {body.opportunity_title}"
    service = GeminiService()
    try:
        content = await service.generate_document("action-sheet", body.model_dump())
    except GeminiServiceError:
        content = _fallback_action_sheet(body)

    return await _store_document(db, current_user, "action-sheet", title, content, body.model_dump())


@router.post("/patient-letter", response_model=GeneratedDocumentResponse)
async def generate_patient_letter(
    body: PatientLetterRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    title = f"Patient Letter: {body.opportunity_title}"
    service = GeminiService()
    try:
        content = await service.generate_document("patient-letter", body.model_dump())
    except GeminiServiceError:
        content = _fallback_patient_letter(body)

    return await _store_document(db, current_user, "patient-letter", title, content, body.model_dump())


@router.post("/sms", response_model=GeneratedDocumentResponse)
async def generate_sms(
    body: SMSRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    title = f"SMS: {body.practice_name}"
    service = GeminiService()
    try:
        content = (await service.generate_document("sms", body.model_dump())).strip()
    except GeminiServiceError:
        content = _fallback_sms(body)

    return await _store_document(db, current_user, "sms", title, content[:160], body.model_dump())


@router.get("/{document_id}", response_model=StoredDocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    result = await db.execute(
        select(AIDecisionAudit).where(
            AIDecisionAudit.id == doc_uuid,
            AIDecisionAudit.tenant_id == current_user.tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    metadata = record.extra or {}
    if metadata.get("document_type") not in {"action-sheet", "patient-letter", "sms"}:
        raise HTTPException(status_code=404, detail="Document not found")

    return StoredDocumentResponse(
        document_id=record.id,
        document_type=str(metadata.get("document_type")),
        title=str(metadata.get("title", "Generated Document")),
        content=str(metadata.get("content", record.output_summary or "")),
        generated_at=record.created_at,
        generated_by_user_id=record.user_id,
        tenant_id=record.tenant_id,
    )
