from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_active_user, get_tenant_id
from app.models.org import ODSOrganisation
from app.config import settings

router = APIRouter(prefix="/practices", tags=["Practices"])


@router.get("/")
async def list_practices(
    search: Optional[str] = Query(None, description="Search by name or ODS code"),
    sub_icb_ods: Optional[str] = Query(None, description="Filter by Sub-ICB ODS code e.g. 02P"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """List all practices for this tenant (South Yorkshire = 105 practices)."""
    tenant_id = current_user.tenant_id or settings.SY_TENANT_ID

    query = select(ODSOrganisation).where(
        ODSOrganisation.tenant_id == tenant_id,
        ODSOrganisation.org_type == "PRACTICE",
        ODSOrganisation.status == "active",
    )

    if search:
        query = query.where(
            ODSOrganisation.name.ilike(f"%{search}%") |
            ODSOrganisation.ods_code.ilike(f"%{search}%")
        )
    if sub_icb_ods:
        query = query.where(ODSOrganisation.parent_ods_code == sub_icb_ods)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(ODSOrganisation.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    practices = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "ods_code": p.ods_code,
                "name": p.name,
                "address": p.address,
                "postcode": p.postcode,
                "parent_ods_code": p.parent_ods_code,
                "status": p.status,
            }
            for p in practices
        ],
    }


@router.get("/search")
async def search_practices(
    q: str = Query(..., min_length=2, description="Practice name or ODS code"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Fast practice search — used by action sheet form autocomplete."""
    tenant_id = current_user.tenant_id or settings.SY_TENANT_ID
    result = await db.execute(
        select(ODSOrganisation)
        .where(
            ODSOrganisation.tenant_id == tenant_id,
            ODSOrganisation.org_type == "PRACTICE",
            ODSOrganisation.name.ilike(f"%{q}%") | ODSOrganisation.ods_code.ilike(f"%{q}%"),
        )
        .limit(10)
    )
    practices = result.scalars().all()
    return [{"ods_code": p.ods_code, "name": p.name, "postcode": p.postcode} for p in practices]


@router.get("/{ods_code}")
async def get_practice(
    ods_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Get full detail for a single practice."""
    result = await db.execute(
        select(ODSOrganisation).where(ODSOrganisation.ods_code == ods_code.upper())
    )
    practice = result.scalar_one_or_none()
    if not practice:
        raise HTTPException(status_code=404, detail=f"Practice {ods_code} not found")

    return {
        "ods_code": practice.ods_code,
        "name": practice.name,
        "address": practice.address,
        "postcode": practice.postcode,
        "phone": practice.phone,
        "parent_ods_code": practice.parent_ods_code,
        "status": practice.status,
        "last_synced_at": practice.last_synced_at,
    }


@router.get("/{ods_code}/opportunities")
async def get_practice_opportunities(
    ods_code: str,
    current_user=Depends(get_current_active_user),
):
    """Return all MongoDB opportunities for a specific practice."""
    from app.mongo_models.opportunity_mongo import OpportunityDocument
    collection = OpportunityDocument.get_pymongo_collection()
    docs = await collection.find({"practice_ods_code": ods_code.upper()}).to_list(length=100)
    return {
        "practice_ods_code": ods_code,
        "total": len(docs),
        "opportunities": [
            {
                "id": str(d["_id"]),
                "workstream": d.get("workstream"),
                "estimated_annual_savings": d.get("estimated_annual_savings", 0),
                "status": d.get("status"),
                "description": d.get("description"),
            }
            for d in docs
        ],
    }
