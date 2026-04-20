from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Alert, Branch, Incident, Metric
from schemas import AlertVolumeByBranch, BankOpsKpis, DashboardSummary, MetricRead

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


@router.get("/dashboard/bank-ops-kpis", response_model=BankOpsKpis)
async def dashboard_bank_ops_kpis(db: AsyncSession = Depends(get_db)):
    now_utc = datetime.now(timezone.utc)
    last_day = now_utc - timedelta(days=1)
    last_hour = now_utc - timedelta(hours=1)

    latest_metrics_result = await db.execute(
        select(Metric).order_by(Metric.recorded_at.desc(), Metric.id.desc()).limit(5000)
    )
    latest_metrics_rows = list(latest_metrics_result.scalars().all())

    latest_metric_by_branch: dict[int, Metric] = {}
    for metric in latest_metrics_rows:
        if metric.branch_id not in latest_metric_by_branch:
            latest_metric_by_branch[metric.branch_id] = metric

    latest_metrics = list(latest_metric_by_branch.values())

    if latest_metrics:
        transaction_scores: list[float] = []
        transfer_latencies: list[float] = []
        transfer_error_rates: list[float] = []
        network_up_values: list[int] = []
        replication_lag_values: list[float] = []

        for metric in latest_metrics:
            infra_down_penalty = 0.0
            if not metric.core_banking_service_up:
                infra_down_penalty += 28.0
            if not metric.network_up:
                infra_down_penalty += 22.0
            if not metric.postgres_db_up:
                infra_down_penalty += 18.0

            resource_penalty = (
                max(0.0, metric.cpu_usage - 75.0) * 0.35
                + max(0.0, metric.ram_usage - 80.0) * 0.28
                + max(0.0, metric.disk_usage - 85.0) * 0.2
            )

            transaction_score = max(0.0, min(100.0, 99.5 - infra_down_penalty - resource_penalty))
            transaction_scores.append(transaction_score)

            latency_ms = (
                95.0
                + metric.cpu_usage * 2.1
                + metric.ram_usage * 1.4
                + (0.0 if metric.network_up else 800.0)
                + (0.0 if metric.core_banking_service_up else 1200.0)
                + (0.0 if metric.postgres_db_up else 650.0)
                + max(0.0, metric.disk_usage - 85.0) * 8.0
            )
            transfer_latencies.append(latency_ms)

            error_rate = min(
                100.0,
                0.25
                + max(0.0, metric.cpu_usage - 70.0) * 0.09
                + max(0.0, metric.ram_usage - 75.0) * 0.06
                + max(0.0, metric.disk_usage - 85.0) * 0.05
                + (15.0 if not metric.network_up else 0.0)
                + (20.0 if not metric.core_banking_service_up else 0.0)
                + (10.0 if not metric.postgres_db_up else 0.0),
            )
            transfer_error_rates.append(error_rate)

            network_up_values.append(1 if metric.network_up else 0)

            replication_lag = max(
                0.0,
                max(0.0, metric.disk_usage - 70.0) * 0.8
                + max(0.0, metric.cpu_usage - 75.0) * 0.5
                + (90.0 if not metric.postgres_db_up else 0.0),
            )
            replication_lag_values.append(replication_lag)

        transfer_latencies.sort()
        p95_index = max(0, int(round((len(transfer_latencies) - 1) * 0.95)))

        transaction_success_rate = round(sum(transaction_scores) / len(transaction_scores), 2)
        transfer_p95_latency = round(transfer_latencies[p95_index], 2)
        transfer_error_rate = round(sum(transfer_error_rates) / len(transfer_error_rates), 2)
        atm_pos_network_uptime = round((sum(network_up_values) / len(network_up_values)) * 100.0, 2)
        db_replication_lag_seconds = round(sum(replication_lag_values) / len(replication_lag_values), 2)
    else:
        transaction_success_rate = 100.0
        transfer_p95_latency = 0.0
        transfer_error_rate = 0.0
        atm_pos_network_uptime = 100.0
        db_replication_lag_seconds = 0.0

    auth_failures_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.fired_at >= last_hour,
            Alert.alert_type.in_(["service_down", "high_cpu", "high_ram", "disk_full"]),
        )
    )
    authentication_failures_last_hour = int(auth_failures_result.scalar_one() or 0)

    alert_volume_rows = (
        await db.execute(
            select(
                Branch.id.label("branch_id"),
                Branch.name.label("branch_name"),
                func.coalesce(
                    func.sum(case((Alert.severity == "critical", 1), else_=0)),
                    0,
                ).label("critical"),
                func.coalesce(
                    func.sum(case((Alert.severity == "warning", 1), else_=0)),
                    0,
                ).label("warning"),
                func.coalesce(
                    func.sum(case((Alert.severity == "info", 1), else_=0)),
                    0,
                ).label("info"),
                func.count(Alert.id).label("total"),
            )
            .select_from(Branch)
            .join(Alert, Alert.branch_id == Branch.id)
            .where(Alert.fired_at >= last_day)
            .group_by(Branch.id, Branch.name)
            .order_by(func.count(Alert.id).desc(), Branch.name.asc())
            .limit(8)
        )
    ).all()

    alert_volume_by_branch = [
        AlertVolumeByBranch(
            branch_id=int(row.branch_id),
            branch_name=row.branch_name,
            critical=int(row.critical),
            warning=int(row.warning),
            info=int(row.info),
            total=int(row.total),
        )
        for row in alert_volume_rows
    ]

    return BankOpsKpis(
        transaction_success_rate_percent=transaction_success_rate,
        authentication_failures_last_hour=authentication_failures_last_hour,
        transfer_p95_latency_ms=transfer_p95_latency,
        transfer_error_rate_percent=transfer_error_rate,
        atm_pos_network_uptime_percent=atm_pos_network_uptime,
        db_replication_lag_seconds=db_replication_lag_seconds,
        alert_volume_by_branch=alert_volume_by_branch,
    )
