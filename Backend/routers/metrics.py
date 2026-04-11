from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud import (
    create_metric,
    get_branch,
    get_latest_metric,
    get_metric_history,
    list_branches,
)
from database import get_db
from models import Branch, Metric
from schemas import DashboardSummary, MetricCreate, MetricRead

router = APIRouter(prefix="", tags=["metrics"])


@router.get("/metrics/{branch_id}", response_model=MetricRead)
async def read_latest_metric(branch_id: int, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    metric = await get_latest_metric(db, branch_id)
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No metrics found for branch")
    return metric


@router.get("/metrics/{branch_id}/history", response_model=list[MetricRead])
async def read_metric_history(branch_id: int, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return await get_metric_history(db, branch_id, limit=60)


@router.post("/metrics/{branch_id}", response_model=MetricRead, status_code=status.HTTP_201_CREATED)
async def post_metric(branch_id: int, payload: MetricCreate, db: AsyncSession = Depends(get_db)):
    branch = await get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return await create_metric(db, branch, payload)


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    branches = await list_branches(db)
    active_alerts_count = 0
    incidents_today = 0
    uptime_values: list[float] = []

    from crud import active_alerts, list_incidents

    active_alerts_count = len(await active_alerts(db))
    today = datetime.now(timezone.utc).date()

    incidents_result, _ = await list_incidents(db, page=1, page_size=1000)
    incidents_today = sum(1 for incident in incidents_result if incident.started_at.date() == today)

    for branch in branches:
        branch_history = await get_metric_history(db, branch.id, limit=60)
        if not branch_history:
            continue
        uptime_ratio = sum(1 for metric in branch_history if metric.core_banking_service_up) / len(branch_history)
        uptime_values.append(round(uptime_ratio * 100, 2))

    avg_uptime = round(sum(uptime_values) / len(uptime_values), 2) if uptime_values else 0.0
    return DashboardSummary(
        total_branches=len(branches),
        active_alerts=active_alerts_count,
        incidents_today=incidents_today,
        avg_uptime_percent=avg_uptime,
    )
