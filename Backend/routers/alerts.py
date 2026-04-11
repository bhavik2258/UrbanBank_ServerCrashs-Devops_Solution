from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud import active_alerts, create_alert, get_branch, resolve_alert
from database import get_db
from models import Alert
from schemas import AlertCreate, AlertRead, AlertResolveResponse

router = APIRouter(prefix="", tags=["alerts"])


@router.get("/alerts", response_model=list[AlertRead])
async def read_alerts(
    branch_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await active_alerts(db, branch_id)


@router.post("/alerts", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def add_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, payload.branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return await create_alert(db, payload)


@router.patch("/alerts/{alert_id}/resolve", response_model=AlertResolveResponse)
async def resolve_existing_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert = await resolve_alert(db, alert)
    return AlertResolveResponse(message="Alert resolved successfully", alert_id=alert.id, resolved=alert.is_resolved)
