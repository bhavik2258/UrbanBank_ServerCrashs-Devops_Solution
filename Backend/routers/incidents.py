from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud import create_incident, get_branch, list_incidents
from database import get_db
from models import Alert, Incident
from schemas import IncidentCreate, IncidentPage, IncidentRead

router = APIRouter(prefix="", tags=["incidents"])


@router.get("/incidents", response_model=IncidentPage)
async def read_incidents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    incidents, total = await list_incidents(db, page=page, page_size=page_size)
    return IncidentPage(
        items=[IncidentRead.model_validate(incident) for incident in incidents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/incidents/{branch_id}", response_model=list[IncidentRead])
async def read_branch_incidents(branch_id: int, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    incidents, _ = await list_incidents(db, branch_id=branch_id, page=1, page_size=1000)
    return [IncidentRead.model_validate(incident) for incident in incidents]


@router.post("/incidents", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def add_incident(payload: IncidentCreate, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, payload.branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    if payload.alert_id is not None:
        alert_result = await db.execute(select(Alert).where(Alert.id == payload.alert_id))
        if alert_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return await create_incident(db, payload)
