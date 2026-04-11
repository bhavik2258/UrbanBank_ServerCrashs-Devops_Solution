from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Alert, AlertSeverity, AlertType, Branch, BranchStatus, Incident, Metric
from schemas import AlertCreate, IncidentCreate, MetricCreate

BRANCH_SEEDS = [
    {
        "name": "Mumbai",
        "ip_address": "10.0.1.11",
        "location": "Mumbai, Maharashtra",
        "status": BranchStatus.healthy,
        "metric": {
            "cpu_usage": 28.4,
            "ram_usage": 49.8,
            "disk_usage": 61.2,
            "core_banking_service_up": True,
            "postgres_db_up": True,
            "network_up": True,
        },
    },
    {
        "name": "Pune",
        "ip_address": "10.0.1.12",
        "location": "Pune, Maharashtra",
        "status": BranchStatus.warning,
        "metric": {
            "cpu_usage": 78.9,
            "ram_usage": 71.3,
            "disk_usage": 66.5,
            "core_banking_service_up": True,
            "postgres_db_up": True,
            "network_up": True,
        },
    },
    {
        "name": "Nashik",
        "ip_address": "10.0.1.13",
        "location": "Nashik, Maharashtra",
        "status": BranchStatus.healthy,
        "metric": {
            "cpu_usage": 34.2,
            "ram_usage": 52.1,
            "disk_usage": 45.9,
            "core_banking_service_up": True,
            "postgres_db_up": True,
            "network_up": True,
        },
    },
]


def derive_branch_status(metric: Metric | MetricCreate) -> str:
    """Derive a branch status from the latest metric snapshot."""
    if not metric.core_banking_service_up or not metric.postgres_db_up or not metric.network_up:
        return BranchStatus.critical.value
    if metric.cpu_usage >= 75 or metric.ram_usage >= 80 or metric.disk_usage >= 85:
        return BranchStatus.warning.value
    return BranchStatus.healthy.value


async def get_branch(session: AsyncSession, branch_id: int) -> Branch | None:
    result = await session.execute(select(Branch).where(Branch.id == branch_id))
    return result.scalar_one_or_none()


async def get_branch_by_name(session: AsyncSession, name: str) -> Branch | None:
    result = await session.execute(select(Branch).where(Branch.name == name))
    return result.scalar_one_or_none()


async def get_latest_metric(session: AsyncSession, branch_id: int) -> Metric | None:
    result = await session.execute(
        select(Metric)
        .where(Metric.branch_id == branch_id)
        .order_by(Metric.recorded_at.desc(), Metric.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_metric_history(session: AsyncSession, branch_id: int, limit: int = 60) -> list[Metric]:
    result = await session.execute(
        select(Metric)
        .where(Metric.branch_id == branch_id)
        .order_by(Metric.recorded_at.desc(), Metric.id.desc())
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def list_branches(session: AsyncSession) -> list[Branch]:
    result = await session.execute(select(Branch).order_by(Branch.id.asc()))
    return list(result.scalars().all())


async def create_branch(session: AsyncSession, payload: dict[str, object]) -> Branch:
    branch = Branch(**payload)
    if isinstance(branch.status, BranchStatus):
        branch.status = branch.status.value
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


async def create_metric(session: AsyncSession, branch: Branch, payload: MetricCreate) -> Metric:
    metric = Metric(branch_id=branch.id, **payload.model_dump())
    session.add(metric)
    branch.status = derive_branch_status(metric)
    await session.commit()
    await session.refresh(metric)
    await session.refresh(branch)
    return metric


async def create_alert(session: AsyncSession, payload: AlertCreate) -> Alert:
    alert = Alert(**payload.model_dump())
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


async def create_incident(session: AsyncSession, payload: IncidentCreate) -> Incident:
    data = payload.model_dump()
    if data.get("started_at") is None:
        data["started_at"] = datetime.now(timezone.utc)
    incident = Incident(**data)
    session.add(incident)
    await session.commit()
    await session.refresh(incident)
    return incident


async def resolve_alert(session: AsyncSession, alert: Alert) -> Alert:
    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(alert)
    return alert


async def active_alerts(session: AsyncSession, branch_id: int | None = None) -> list[Alert]:
    query = select(Alert).where(Alert.is_resolved.is_(False)).order_by(Alert.fired_at.desc())
    if branch_id is not None:
        query = query.where(Alert.branch_id == branch_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def list_alerts(session: AsyncSession, branch_id: int | None = None) -> list[Alert]:
    query = select(Alert).order_by(Alert.fired_at.desc())
    if branch_id is not None:
        query = query.where(Alert.branch_id == branch_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def list_incidents(
    session: AsyncSession,
    branch_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Incident], int]:
    query = select(Incident).order_by(Incident.started_at.desc(), Incident.id.desc())
    count_query = select(func.count(Incident.id))
    if branch_id is not None:
        query = query.where(Incident.branch_id == branch_id)
        count_query = count_query.where(Incident.branch_id == branch_id)
    total = await session.scalar(count_query) or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    return list(result.scalars().all()), total


async def get_open_incident(session: AsyncSession, branch_id: int) -> Incident | None:
    result = await session.execute(
        select(Incident)
        .where(and_(Incident.branch_id == branch_id, Incident.resolved_at.is_(None)))
        .order_by(Incident.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def resolve_incident(session: AsyncSession, incident: Incident, auto_healed: bool) -> Incident:
    incident.auto_healed = auto_healed
    incident.resolved_at = datetime.now(timezone.utc)
    incident.duration_minutes = round(
        (incident.resolved_at - incident.started_at).total_seconds() / 60.0, 2
    )
    await session.commit()
    await session.refresh(incident)
    return incident


async def branch_upsert_metric_state(
    session: AsyncSession,
    branch: Branch,
    metric_payload: MetricCreate,
) -> Metric:
    return await create_metric(session, branch, metric_payload)


async def seed_database(session: AsyncSession) -> None:
    result = await session.execute(select(func.count(Branch.id)))
    branch_count = result.scalar_one() or 0
    if branch_count > 0:
        return

    for seed in BRANCH_SEEDS:
        branch = Branch(
            name=seed["name"],
            ip_address=seed["ip_address"],
            location=seed["location"],
            status=seed["status"].value,
        )
        session.add(branch)
        await session.flush()

        metric = seed["metric"]
        session.add(
            Metric(
                branch_id=branch.id,
                cpu_usage=metric["cpu_usage"],
                ram_usage=metric["ram_usage"],
                disk_usage=metric["disk_usage"],
                core_banking_service_up=metric["core_banking_service_up"],
                postgres_db_up=metric["postgres_db_up"],
                network_up=metric["network_up"],
                recorded_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 15)),
            )
        )

    await session.commit()


async def generate_branch_metric(session: AsyncSession, branch: Branch) -> Metric:
    latest_metric = await get_latest_metric(session, branch.id)

    if branch.status == BranchStatus.critical.value:
        cpu_usage = min(100.0, (latest_metric.cpu_usage if latest_metric else 95.0) + random.uniform(-1.5, 2.0))
        ram_usage = min(100.0, (latest_metric.ram_usage if latest_metric else 92.0) + random.uniform(-1.0, 2.0))
        disk_usage = min(100.0, (latest_metric.disk_usage if latest_metric else 88.0) + random.uniform(-0.5, 1.5))
        metric_payload = MetricCreate(
            cpu_usage=round(cpu_usage, 2),
            ram_usage=round(ram_usage, 2),
            disk_usage=round(disk_usage, 2),
            core_banking_service_up=False,
            postgres_db_up=False if random.random() > 0.4 else True,
            network_up=False if random.random() > 0.5 else True,
        )
    else:
        base_cpu = latest_metric.cpu_usage if latest_metric else random.uniform(20.0, 45.0)
        base_ram = latest_metric.ram_usage if latest_metric else random.uniform(30.0, 60.0)
        base_disk = latest_metric.disk_usage if latest_metric else random.uniform(25.0, 65.0)
        cpu_usage = max(0.0, min(100.0, base_cpu + random.uniform(-4.0, 4.5)))
        ram_usage = max(0.0, min(100.0, base_ram + random.uniform(-3.0, 3.5)))
        disk_usage = max(0.0, min(100.0, base_disk + random.uniform(-2.0, 2.0)))
        metric_payload = MetricCreate(
            cpu_usage=round(cpu_usage, 2),
            ram_usage=round(ram_usage, 2),
            disk_usage=round(disk_usage, 2),
            core_banking_service_up=True,
            postgres_db_up=True,
            network_up=True,
        )

    return await create_metric(session, branch, metric_payload)


async def ensure_branch_state(session: AsyncSession, branch: Branch) -> Branch:
    latest_metric = await get_latest_metric(session, branch.id)
    if not latest_metric:
        return branch

    branch.status = derive_branch_status(latest_metric)

    await session.commit()
    await session.refresh(branch)
    return branch


async def create_failure_records(session: AsyncSession, branch: Branch) -> tuple[Alert, Incident]:
    alert = await active_alerts(session, branch.id)
    active_service_down_alert = next(
        (item for item in alert if item.alert_type == AlertType.service_down.value), None
    )
    if active_service_down_alert is None:
        active_service_down_alert = await create_alert(
            session,
            AlertCreate(
                branch_id=branch.id,
                alert_type=AlertType.service_down,
                message="core-banking service is DOWN",
                severity=AlertSeverity.critical,
            ),
        )

    incident = await get_open_incident(session, branch.id)
    if incident is None:
        incident = await create_incident(
            session,
            IncidentCreate(
                branch_id=branch.id,
                alert_id=active_service_down_alert.id,
                description="core-banking service crashed and requires auto-heal",
                auto_healed=False,
                heal_action="Restarted core-banking-svc via Ansible auto-heal",
            ),
        )
    return active_service_down_alert, incident


async def heal_branch(session: AsyncSession, branch: Branch) -> tuple[Metric, Alert | None, Incident | None]:
    latest_metric = await get_latest_metric(session, branch.id)
    cpu_usage = latest_metric.cpu_usage if latest_metric else random.uniform(24.0, 40.0)
    ram_usage = latest_metric.ram_usage if latest_metric else random.uniform(30.0, 55.0)
    disk_usage = latest_metric.disk_usage if latest_metric else random.uniform(25.0, 60.0)

    healed_metric = await create_metric(
        session,
        branch,
        MetricCreate(
            cpu_usage=round(max(0.0, min(100.0, cpu_usage - random.uniform(8.0, 18.0))), 2),
            ram_usage=round(max(0.0, min(100.0, ram_usage - random.uniform(5.0, 12.0))), 2),
            disk_usage=round(disk_usage, 2),
            core_banking_service_up=True,
            postgres_db_up=True,
            network_up=True,
        ),
    )

    open_alerts = await active_alerts(session, branch.id)
    service_alert = next((item for item in open_alerts if item.alert_type == AlertType.service_down.value), None)
    resolved_alert = None
    if service_alert is not None:
        resolved_alert = await resolve_alert(session, service_alert)

    open_incident = await get_open_incident(session, branch.id)
    resolved_incident = None
    if open_incident is not None:
        resolved_incident = await resolve_incident(session, open_incident, auto_healed=True)

    branch.status = BranchStatus.healthy.value
    await session.commit()
    await session.refresh(branch)
    return healed_metric, resolved_alert, resolved_incident
