from __future__ import annotations
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Alert
from schemas import AlertRead, AlertResolveResponse

router = APIRouter(prefix="", tags=["alerts"])


@router.get("/alerts", response_model=list[AlertRead])
async def read_alerts(
    branch_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Alert).order_by(Alert.fired_at.desc())
    if branch_id is not None:
        query = query.where(Alert.branch_id == branch_id)

    result = await db.execute(query)
    alerts = list(result.scalars().all())
    return alerts


@router.patch("/alerts/{alert_id}/resolve", response_model=AlertResolveResponse)
async def resolve_alert_route(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    if not alert.is_resolved:
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        db.add(alert)
        await db.commit()

    return AlertResolveResponse(
        message="Alert resolved",
        alert_id=alert.id,
        resolved=True,
    )


@router.get("/alerts/active", response_model=list[AlertRead])
async def read_active_alerts(
    branch_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    from crud import get_active_alerts

    alerts = await get_active_alerts(db, branch_id)
    return alerts
