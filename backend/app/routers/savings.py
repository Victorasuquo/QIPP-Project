from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.intervention import RealizedSavingMonthly, Intervention

router = APIRouter(prefix="/savings", tags=["Savings"])


@router.get("/summary")
async def get_savings_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Total realized savings YTD and by workstream."""
    # Total realized from monthly table
    ytd_result = await db.execute(
        select(func.coalesce(func.sum(RealizedSavingMonthly.realized_saving), 0)).where(
            RealizedSavingMonthly.tenant_id == current_user.tenant_id,
        )
    )
    ytd_total = float(ytd_result.scalar_one() or 0)

    # By workstream
    ws_result = await db.execute(
        select(RealizedSavingMonthly.workstream_name, func.sum(RealizedSavingMonthly.realized_saving))
        .where(RealizedSavingMonthly.tenant_id == current_user.tenant_id)
        .group_by(RealizedSavingMonthly.workstream_name)
        .order_by(func.sum(RealizedSavingMonthly.realized_saving).desc())
    )
    by_workstream = {row[0] or "OTHER": round(float(row[1]), 2) for row in ws_result}

    # Total forecast from interventions
    forecast_result = await db.execute(
        select(func.coalesce(func.sum(Intervention.forecast_annual_savings), 0)).where(
            Intervention.tenant_id == current_user.tenant_id,
        )
    )
    total_forecast = float(forecast_result.scalar_one() or 0)

    return {
        "ytd_total": round(ytd_total, 2),
        "total_forecast": round(total_forecast, 2),
        "by_workstream": by_workstream,
    }


@router.get("/monthly")
async def get_monthly_savings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Monthly savings trend — for the savings chart in the dashboard."""
    result = await db.execute(
        select(RealizedSavingMonthly.period, func.sum(RealizedSavingMonthly.realized_saving))
        .where(RealizedSavingMonthly.tenant_id == current_user.tenant_id)
        .group_by(RealizedSavingMonthly.period)
        .order_by(RealizedSavingMonthly.period)
    )
    return {
        "monthly": [
            {"period": row[0], "amount": round(float(row[1]), 2)} for row in result
        ]
    }
