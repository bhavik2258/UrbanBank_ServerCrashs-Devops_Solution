from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from database import get_db
from models import Branch, Metric
from schemas import (
    BranchRead,
    SimulationResponse,
)

router = APIRouter(prefix="", tags=["branches"])


def _branch_snapshot_query():
    latest_metric = aliased(Metric)
    recent_metric = aliased(Metric)

    latest_metric_id_subquery = (
        select(latest_metric.id)
        .where(latest_metric.branch_id == Branch.id)
        .order_by(latest_metric.recorded_at.desc(), latest_metric.id.desc())
        .limit(1)
        .correlate(Branch)
        .scalar_subquery()
    )

    recent_core_status_subquery = (
        select(recent_metric.core_banking_service_up.label("core_banking_service_up"))
        .where(recent_metric.branch_id == Branch.id)
        .order_by(recent_metric.recorded_at.desc(), recent_metric.id.desc())
        .limit(60)
        .correlate(Branch)
        .subquery()
    )

    uptime_percent_subquery = (
        select(
            func.avg(
                case(
                    (recent_core_status_subquery.c.core_banking_service_up.is_(True), 1),
                    else_=0,
                )
            )
            * 100.0
        )
        .scalar_subquery()
    )

    return (
        select(
            Branch.id.label("id"),
            Branch.name.label("name"),
            Branch.bank_name.label("bank_name"),
            Branch.ip_address.label("ip_address"),
            Branch.location.label("location"),
            Branch.status.label("status"),
            Branch.created_at.label("created_at"),
            func.coalesce(uptime_percent_subquery, 100.0).label("uptime_percent"),
            Metric.id.label("metric_id"),
            Metric.cpu_usage.label("cpu_usage"),
            Metric.ram_usage.label("ram_usage"),
            Metric.disk_usage.label("disk_usage"),
            Metric.core_banking_service_up.label("core_banking_service_up"),
            Metric.postgres_db_up.label("postgres_db_up"),
            Metric.network_up.label("network_up"),
            Metric.recorded_at.label("recorded_at"),
        )
        .outerjoin(Metric, Metric.id == latest_metric_id_subquery)
    )


def _row_to_branch_read(row) -> dict:
    latest_metric = None
    if row.metric_id is not None:
        latest_metric = {
            "id": row.metric_id,
            "branch_id": row.id,
            "cpu_usage": row.cpu_usage,
            "ram_usage": row.ram_usage,
            "disk_usage": row.disk_usage,
            "core_banking_service_up": row.core_banking_service_up,
            "postgres_db_up": row.postgres_db_up,
            "network_up": row.network_up,
            "recorded_at": row.recorded_at,
        }

    uptime_percent = 100.0 if row.uptime_percent is None else round(float(row.uptime_percent), 2)
    return {
        "id": row.id,
        "name": row.name,
        "bank_name": row.bank_name,
        "ip_address": row.ip_address,
        "location": row.location,
        "status": row.status,
        "created_at": row.created_at,
        "uptime_percent": uptime_percent,
        "latest_metric": latest_metric,
    }


@router.get("/branches", response_model=list[BranchRead])
async def read_branches(db: AsyncSession = Depends(get_db)):
    query = _branch_snapshot_query().order_by(Branch.name)
    rows = (await db.execute(query)).all()
    return [_row_to_branch_read(row) for row in rows]


@router.get("/branches/{branch_id}", response_model=BranchRead)
async def read_branch(branch_id: int, db: AsyncSession = Depends(get_db)):
    query = _branch_snapshot_query().where(Branch.id == branch_id)
    row = (await db.execute(query)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    return _row_to_branch_read(row)


@router.post("/simulate/incident/{branch_id}", response_model=SimulationResponse)
async def simulate_incident(branch_id: int, db: AsyncSession = Depends(get_db)):
    from crud import get_branch, simulate_branch_failure

    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")

    metric, alert, incident = await simulate_branch_failure(db, branch)
    return SimulationResponse(
        message="Simulated incident created successfully",
        branch_id=branch_id,
        branch_status=branch.status,
        alert_id=alert.id,
        incident_id=incident.id,
    )

@router.post("/simulate/heal/{branch_id}", response_model=SimulationResponse)
async def simulate_heal(branch_id: int, db: AsyncSession = Depends(get_db)):
    from crud import get_branch, heal_branch

    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")

    metric, alert, incident = await heal_branch(db, branch)
    return SimulationResponse(
        message="Auto-heal completed successfully",
        branch_id=branch_id,
        branch_status=branch.status,
    )
