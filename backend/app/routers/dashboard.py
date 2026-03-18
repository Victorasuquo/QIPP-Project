from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_active_user, get_tenant_id
from app.schemas.common import DashboardSummary, WorkstreamSummary
from app.mongo_models.opportunity_mongo import OpportunityDocument
from app.config import settings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Returns live hero metrics for the QIPP dashboard.
    Queries MongoDB opportunities + PostgreSQL interventions.
    """
    tenant_id = str(current_user.tenant_id) if current_user.tenant_id else settings.SY_TENANT_ID

    # ── 1. Aggregate from MongoDB opportunities ───────────────────────────────
    pipeline = [
        {"$match": {"icb_id": tenant_id, "status": {"$in": ["IDENTIFIED", "APPROVED", "IN_PROGRESS"]}}},
        {"$group": {
            "_id": "$workstream",
            "total_savings": {"$sum": "$estimated_annual_savings"},
            "count": {"$sum": 1},
            "total_patients": {"$sum": "$patients_affected"},
            "top_description": {"$first": "$description"},
        }},
        {"$sort": {"total_savings": -1}},
    ]

    collection = OpportunityDocument.get_pymongo_collection()
    cursor = collection.aggregate(pipeline)
    workstream_data = await cursor.to_list(length=50)

    total_saving_potential = sum(w["total_savings"] for w in workstream_data)
    active_opportunities = sum(w["count"] for w in workstream_data)

    workstream_breakdown = [
        WorkstreamSummary(
            workstream=w["_id"] or "OTHER",
            total_savings=round(w["total_savings"], 2),
            opportunity_count=w["count"],
            patients_affected=w.get("total_patients", 0),
            top_opportunity_description=w.get("top_description"),
        )
        for w in workstream_data
    ]

    # ── 2. Completed switches from PostgreSQL interventions ───────────────────
    from app.models.intervention import Intervention
    result = await db.execute(
        select(func.count()).where(
            Intervention.tenant_id == current_user.tenant_id,
            Intervention.status == "COMPLETED",
        )
    )
    completed_switches = result.scalar_one_or_none() or 0

    # ── 3. Realized savings YTD from PostgreSQL ───────────────────────────────
    from app.models.intervention import RealizedSavingMonthly
    ytd_result = await db.execute(
        select(func.coalesce(func.sum(RealizedSavingMonthly.realized_saving), 0)).where(
            RealizedSavingMonthly.tenant_id == current_user.tenant_id,
        )
    )
    realized_savings_ytd = float(ytd_result.scalar_one() or 0)

    # ── 4. Practice count from ods_organisations ──────────────────────────────
    from app.models.org import ODSOrganisation
    practice_result = await db.execute(
        select(func.count()).where(
            ODSOrganisation.tenant_id == current_user.tenant_id,
            ODSOrganisation.org_type == "PRACTICE",
        )
    )
    total_practices = practice_result.scalar_one_or_none() or 0

    from datetime import datetime
    return DashboardSummary(
        total_saving_potential=round(total_saving_potential, 2),
        active_opportunities=active_opportunities,
        total_practices=total_practices,
        completed_switches=completed_switches,
        realized_savings_ytd=realized_savings_ytd,
        workstream_breakdown=workstream_breakdown,
        data_as_of=datetime.utcnow().strftime("%Y-%m-%d"),
    )
