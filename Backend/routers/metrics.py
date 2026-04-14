from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Alert, Branch, Incident, Metric
from schemas import DashboardSummary, MetricRead

router = APIRouter(prefix="", tags=["metrics"])


@router.get("/metrics/{branch_id}", response_model=MetricRead)
async def read_latest_metric(branch_id: int, db: AsyncSession = Depends(get_db)):
    from crud import get_branch, get_latest_metrics

    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")

    latest_metrics = await get_latest_metrics(db, branch_id, limit=1)
    if not latest_metrics:
        raise HTTPException(status_code=404, detail="No metrics found for branch")

    return latest_metrics[0]


@router.get("/metrics/{branch_id}/history", response_model=list[MetricRead])
async def read_metric_history(branch_id: int, db: AsyncSession = Depends(get_db)):
    from crud import get_branch, get_latest_metrics

    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")

    metrics = await get_latest_metrics(db, branch_id, limit=60)
    # Frontend chart renders better with chronological order.
    return list(reversed(metrics))


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    total_branches = (await db.execute(select(func.count(Branch.id)))).scalar_one()
    active_alerts_count = (
        await db.execute(select(func.count(Alert.id)).where(Alert.is_resolved == False))
    ).scalar_one()

    now_utc = datetime.now(timezone.utc)
    day_start = datetime.combine(now_utc.date(), datetime.min.time(), tzinfo=timezone.utc)
    next_day_start = day_start + timedelta(days=1)
    incidents_today = (
        await db.execute(
            select(func.count(Incident.id)).where(
                Incident.started_at >= day_start,
                Incident.started_at < next_day_start,
            )
        )
    ).scalar_one()

    recent_core_status_subquery = (
        select(Metric.core_banking_service_up.label("core_banking_service_up"))
        .where(Metric.branch_id == Branch.id)
        .order_by(Metric.recorded_at.desc(), Metric.id.desc())
        .limit(60)
        .subquery()
    )

    uptime_rows = (
        await db.execute(
            select(
                func.coalesce(
                    select(
                        func.avg(
                            case(
                                (recent_core_status_subquery.c.core_banking_service_up.is_(True), 1),
                                else_=0,
                            )
                        )
                        * 100.0
                    ).scalar_subquery(),
                    100.0,
                ).label("uptime_percent")
            ).select_from(Branch)
        )
    ).all()

    avg_uptime_scalar = None
    if uptime_rows:
        avg_uptime_scalar = sum(float(row.uptime_percent) for row in uptime_rows) / len(uptime_rows)
    avg_uptime = 100.0 if avg_uptime_scalar is None else round(float(avg_uptime_scalar), 2)
    
    return DashboardSummary(
        total_branches=total_branches,
        active_alerts=active_alerts_count,
        incidents_today=incidents_today,
        avg_uptime_percent=avg_uptime,
    )
