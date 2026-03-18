from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from bson import ObjectId

from app.dependencies import get_current_active_user
from app.mongo_models.opportunity_mongo import OpportunityDocument
from app.schemas.common import OpportunityResponse, OpportunityListResponse

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


def _doc_to_response(doc: OpportunityDocument) -> OpportunityResponse:
    return OpportunityResponse(
        id=str(doc.id),
        workstream=doc.workstream,
        description=doc.description,
        estimated_annual_savings=doc.estimated_annual_savings,
        patients_affected=doc.patients_affected,
        status=doc.status,
        org_level=doc.org_level,
        practice_ods_code=doc.practice_ods_code,
        pcn_ods_code=doc.pcn_ods_code,
        sub_icb_ods_code=doc.sub_icb_ods_code,
        therapeutic_area=doc.therapeutic_area,
        effort_reward_score=doc.effort_reward_score,
        priority_rank=doc.priority_rank,
        current_expensive_bnf=doc.current_expensive_bnf,
        target_cheap_bnf=doc.target_cheap_bnf,
    )


@router.get("/", response_model=OpportunityListResponse)
async def list_opportunities(
    workstream: Optional[str] = Query(None, description="Filter by workstream e.g. DPP4, SGLT2"),
    status: Optional[str] = Query(None, description="Filter by status e.g. IDENTIFIED, APPROVED"),
    org_level: Optional[str] = Query(None, description="icb | sub_icb | pcn | practice"),
    practice_ods_code: Optional[str] = Query(None),
    pcn_ods_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("estimated_annual_savings", description="Field to sort by"),
    current_user=Depends(get_current_active_user),
):
    """List all opportunities with filtering and pagination."""
    from app.config import settings

    filters: dict = {}
    tenant_id = str(current_user.tenant_id) if current_user.tenant_id else settings.SY_TENANT_ID
    filters["icb_id"] = tenant_id

    if workstream:
        filters["workstream"] = workstream.upper()
    if status:
        filters["status"] = status.upper()
    if org_level:
        filters["org_level"] = org_level
    if practice_ods_code:
        filters["practice_ods_code"] = practice_ods_code
    if pcn_ods_code:
        filters["pcn_ods_code"] = pcn_ods_code

    collection = OpportunityDocument.get_pymongo_collection()
    total = await collection.count_documents(filters)
    skip = (page - 1) * page_size

    sort_direction = -1  # descending
    cursor = collection.find(filters).sort(sort_by, sort_direction).skip(skip).limit(page_size)
    raw_docs = await cursor.to_list(length=page_size)

    items = []
    for raw in raw_docs:
        doc = OpportunityDocument.model_validate(raw)
        items.append(_doc_to_response(doc))

    return OpportunityListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/summary")
async def opportunities_summary(current_user=Depends(get_current_active_user)):
    """Aggregate total savings potential grouped by workstream."""
    from app.config import settings
    tenant_id = str(current_user.tenant_id) if current_user.tenant_id else settings.SY_TENANT_ID

    pipeline = [
        {"$match": {"icb_id": tenant_id}},
        {"$group": {
            "_id": "$workstream",
            "total_savings": {"$sum": "$estimated_annual_savings"},
            "count": {"$sum": 1},
            "patients": {"$sum": "$patients_affected"},
        }},
        {"$sort": {"total_savings": -1}},
    ]
    collection = OpportunityDocument.get_pymongo_collection()
    results = await collection.aggregate(pipeline).to_list(length=50)
    return {
        "workstreams": [
            {
                "workstream": r["_id"],
                "total_savings": round(r["total_savings"], 2),
                "count": r["count"],
                "patients_affected": r["patients"],
            }
            for r in results
        ]
    }


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    current_user=Depends(get_current_active_user),
):
    """Get a single opportunity by MongoDB ObjectId."""
    try:
        oid = ObjectId(opportunity_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid opportunity ID format")

    doc = await OpportunityDocument.get(oid)
    if not doc:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return _doc_to_response(doc)


@router.patch("/{opportunity_id}/status")
async def update_opportunity_status(
    opportunity_id: str,
    new_status: str = Query(..., description="IDENTIFIED | APPROVED | IN_PROGRESS | COMPLETED | REJECTED"),
    current_user=Depends(get_current_active_user),
):
    """Update the status of an opportunity."""
    valid = {"IDENTIFIED", "APPROVED", "IN_PROGRESS", "COMPLETED", "REJECTED"}
    if new_status.upper() not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")

    try:
        oid = ObjectId(opportunity_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid opportunity ID")

    collection = OpportunityDocument.get_pymongo_collection()
    result = await collection.update_one(
        {"_id": oid},
        {"$set": {"status": new_status.upper()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return {"id": opportunity_id, "status": new_status.upper(), "updated": True}
