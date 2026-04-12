from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Branch, Metric
from schemas import (
    BranchRead,
    SimulationResponse,
)

router = APIRouter(prefix="", tags=["branches"])


def _branch_snapshot_query():
    latest_metric_timestamp_subquery = (
        select(
            Metric.branch_id.label("branch_id"),
            func.max(Metric.recorded_at).label("latest_recorded_at"),
        )
        .group_by(Metric.branch_id)
        .subquery()
    )

    latest_metric_subquery = (
        select(
            Metric.branch_id.label("branch_id"),
            Metric.id.label("metric_id"),
            Metric.cpu_usage.label("cpu_usage"),
            Metric.ram_usage.label("ram_usage"),
            Metric.disk_usage.label("disk_usage"),
            Metric.core_banking_service_up.label("core_banking_service_up"),
            Metric.postgres_db_up.label("postgres_db_up"),
            Metric.network_up.label("network_up"),
            Metric.recorded_at.label("recorded_at"),
        )
        .join(
            latest_metric_timestamp_subquery,
            and_(
                Metric.branch_id == latest_metric_timestamp_subquery.c.branch_id,
                Metric.recorded_at == latest_metric_timestamp_subquery.c.latest_recorded_at,
            ),
        )
        .subquery()
    )

    ranked_metrics_subquery = (
        select(
            Metric.branch_id.label("branch_id"),
            Metric.core_banking_service_up.label("core_banking_service_up"),
            func.row_number()
            .over(partition_by=Metric.branch_id, order_by=Metric.recorded_at.desc())
            .label("metric_rank"),
        )
        .subquery()
    )

    uptime_subquery = (
        select(
            ranked_metrics_subquery.c.branch_id,
            (
                func.avg(
                    case(
                        (ranked_metrics_subquery.c.core_banking_service_up.is_(True), 1),
                        else_=0,
                    )
                )
                * 100.0
            ).label("uptime_percent"),
        )
        .where(ranked_metrics_subquery.c.metric_rank <= 60)
        .group_by(ranked_metrics_subquery.c.branch_id)
        .subquery()
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
            uptime_subquery.c.uptime_percent.label("uptime_percent"),
            latest_metric_subquery.c.metric_id.label("metric_id"),
            latest_metric_subquery.c.cpu_usage.label("cpu_usage"),
            latest_metric_subquery.c.ram_usage.label("ram_usage"),
            latest_metric_subquery.c.disk_usage.label("disk_usage"),
            latest_metric_subquery.c.core_banking_service_up.label("core_banking_service_up"),
            latest_metric_subquery.c.postgres_db_up.label("postgres_db_up"),
            latest_metric_subquery.c.network_up.label("network_up"),
            latest_metric_subquery.c.recorded_at.label("recorded_at"),
        )
        .outerjoin(latest_metric_subquery, Branch.id == latest_metric_subquery.c.branch_id)
        .outerjoin(uptime_subquery, Branch.id == uptime_subquery.c.branch_id)
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
