from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.permissions import requires_roles, Role
from app.models.org import ODSOrganisation
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(requires_roles(Role.SYSTEM_ADMIN, Role.ADMIN, Role.ICB_MANAGER)),
):
    """List all users for this tenant (system_admin / admin only)."""
    result = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id).order_by(User.last_name)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role,
            "is_active": u.is_active,
            "practice_ods_code": u.practice_ods_code,
        }
        for u in users
    ]


@router.get("/health/db")
async def db_health(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(requires_roles(Role.SYSTEM_ADMIN, Role.ADMIN)),
):
    """Check database row counts for monitoring."""
    from sqlalchemy import text
    from app.mongo_models.opportunity_mongo import OpportunityDocument

    checks = {}
    for table in ["users", "icbs", "pcns", "ods_organisations", "interventions"]:
        result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
        checks[table] = result.scalar()

    checks["mongo_opportunities"] = await OpportunityDocument.count()
    return {"status": "ok", "counts": checks}


@router.post("/sync-ods/direct")
async def trigger_ods_sync(
    target_icb_ods: str = "QF7",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(requires_roles(Role.SYSTEM_ADMIN, Role.ADMIN)),
):
    """
    Trigger a fresh ODS sync for a specific ICB.
    Calls NHS ODS API and upserts into ods_organisations.
    """
    import httpx
    from datetime import datetime

    ODS_BASE = "https://directory.spineservices.nhs.uk/ORD/2-0-0/organisations"
    loaded = {"sub_icbs": 0, "pcns": 0, "practices": 0, "errors": []}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch sub-ICBs under this ICB
        resp = await client.get(f"{ODS_BASE}?RelTypeId=RE2&TargetOrgId={target_icb_ods}&_format=json")
        if resp.status_code == 200:
            orgs = resp.json().get("Organisations", [])
            for org in orgs:
                ods_code = org.get("OrgId", "")
                name = org.get("Name", "")
                db.add(ODSOrganisation(
                    tenant_id=current_user.tenant_id or settings.SY_TENANT_ID,
                    ods_code=ods_code,
                    name=name.title(),
                    org_type="SUB_ICB",
                    parent_ods_code=target_icb_ods,
                    last_synced_at=datetime.utcnow(),
                ))
                loaded["sub_icbs"] += 1

    await db.commit()
    return {"status": "success", "target_icb": target_icb_ods, "loaded": loaded}
