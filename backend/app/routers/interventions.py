from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.intervention import Intervention, RealizedSavingMonthly
from app.schemas.common import InterventionResponse

router = APIRouter(prefix="/interventions", tags=["Interventions"])


@router.get("/", response_model=list[InterventionResponse])
async def list_interventions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """List all 13 interventions from the V1 database."""
    result = await db.execute(
        select(Intervention)
        .where(Intervention.tenant_id == current_user.tenant_id)
        .order_by(Intervention.forecast_annual_savings.desc())
    )
    interventions = result.scalars().all()
    return [InterventionResponse.model_validate(i) for i in interventions]


@router.get("/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    import uuid
    from fastapi import HTTPException
    result = await db.execute(
        select(Intervention).where(Intervention.id == uuid.UUID(intervention_id))
    )
    intervention = result.scalar_one_or_none()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return InterventionResponse.model_validate(intervention)


@router.patch("/{intervention_id}/status")
async def update_intervention_status(
    intervention_id: str,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    import uuid
    from fastapi import HTTPException
    from datetime import datetime

    valid = {"DRAFT", "APPROVED", "ACTIVE", "COMPLETED", "PAUSED", "CANCELLED"}
    if new_status.upper() not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid}")

    result = await db.execute(
        select(Intervention).where(Intervention.id == uuid.UUID(intervention_id))
    )
    intervention = result.scalar_one_or_none()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    intervention.status = new_status.upper()
    intervention.status_changed_at = datetime.utcnow()
    intervention.status_changed_by = current_user.email
    await db.commit()
    return {"id": intervention_id, "status": new_status.upper()}
