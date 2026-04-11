from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud import (
    create_branch,
    create_failure_records,
    ensure_branch_state,
    get_branch,
    get_latest_metric,
    heal_branch,
    list_branches,
)
from database import get_db
from models import Branch
from schemas import BranchCreate, BranchRead, SimulationResponse

router = APIRouter(prefix="", tags=["branches"])


async def _build_branch_response(session: AsyncSession, branch: Branch) -> BranchRead:
    latest_metric = await get_latest_metric(session, branch.id)
    branch_data = BranchRead.model_validate(branch)
    branch_data.latest_metric = latest_metric
    return branch_data


@router.get("/branches", response_model=list[BranchRead])
async def read_branches(db: AsyncSession = Depends(get_db)):
    branches = await list_branches(db)
    response: list[BranchRead] = []
    for branch in branches:
        response.append(await _build_branch_response(db, branch))
    return response


@router.get("/branches/{branch_id}", response_model=BranchRead)
async def read_branch(branch_id: int, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return await _build_branch_response(db, branch)


@router.post("/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
async def add_branch(payload: BranchCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Branch).where((Branch.name == payload.name) | (Branch.ip_address == payload.ip_address)))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Branch already exists")
    branch = await create_branch(db, payload.model_dump())
    return await _build_branch_response(db, branch)


@router.post("/simulate/failure/{branch_id}", response_model=SimulationResponse)
async def simulate_failure(branch_id: int, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    latest_metric = await get_latest_metric(db, branch.id)
    if latest_metric is not None:
        latest_metric.core_banking_service_up = False
        latest_metric.postgres_db_up = False
        latest_metric.network_up = False
        latest_metric.cpu_usage = min(100.0, max(latest_metric.cpu_usage, 92.0))
        latest_metric.ram_usage = min(100.0, max(latest_metric.ram_usage, 90.0))
        branch.status = "critical"
        await db.commit()

    alert, incident = await create_failure_records(db, branch)
    branch.status = "critical"
    await db.commit()

    return SimulationResponse(
        message="Failure simulated successfully",
        branch_id=branch.id,
        branch_status=branch.status,
        alert_id=alert.id,
        incident_id=incident.id,
    )


@router.post("/simulate/heal/{branch_id}", response_model=SimulationResponse)
async def simulate_heal(branch_id: int, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    healed_metric, resolved_alert, resolved_incident = await heal_branch(db, branch)
    branch = await ensure_branch_state(db, branch)

    return SimulationResponse(
        message="Auto-heal completed successfully",
        branch_id=branch.id,
        branch_status=branch.status,
        alert_id=resolved_alert.id if resolved_alert else None,
        incident_id=resolved_incident.id if resolved_incident else None,
    )
