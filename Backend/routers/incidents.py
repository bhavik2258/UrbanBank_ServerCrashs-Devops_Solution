from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import IncidentRead, IncidentPage

router = APIRouter(prefix="", tags=["incidents"])


@router.get("/incidents", response_model=IncidentPage)
async def read_incidents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    branch_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    from crud import get_incidents

    offset = (page - 1) * page_size
    incidents, total = await get_incidents(db, branch_id=branch_id, limit=page_size, offset=offset)
    return IncidentPage(items=incidents, total=total, page=page, page_size=page_size)


@router.get("/incidents/{branch_id}", response_model=list[IncidentRead])
async def read_incidents_by_branch(branch_id: int, db: AsyncSession = Depends(get_db)):
    from crud import get_branch, get_incidents

    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")

    incidents, _ = await get_incidents(db, branch_id=branch_id, limit=500, offset=0)
    return incidents
