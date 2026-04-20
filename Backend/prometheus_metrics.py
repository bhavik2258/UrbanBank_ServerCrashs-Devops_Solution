from __future__ import annotations

from prometheus_client import Counter, Gauge
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Branch, Incident, BranchStatus

branch_status_total = Counter(
    "branch_status_total",
    "Total branch status transitions recorded by the UrbanBank backend",
    ["status"],
)

branch_status_current = Gauge(
    "branch_status_current",
    "Current number of branches by status in the UrbanBank backend",
    ["status"],
)

incident_created_total = Counter(
    "incident_created_total",
    "Total incidents created by the UrbanBank backend",
)

active_incidents = Gauge(
    "active_incidents",
    "Current number of unresolved incidents in the UrbanBank backend",
)


def initialize_prometheus_metric_labels() -> None:
    for status in BranchStatus:
        branch_status_total.labels(status=status.value)
        branch_status_current.labels(status=status.value)


def record_branch_status(status: BranchStatus | str) -> None:
    branch_status_total.labels(status=status.value if isinstance(status, BranchStatus) else str(status)).inc()


def update_branch_status_current(old_status: BranchStatus | str | None, new_status: BranchStatus | str) -> None:
    normalized_new_status = new_status.value if isinstance(new_status, BranchStatus) else str(new_status)
    if old_status is not None:
        normalized_old_status = old_status.value if isinstance(old_status, BranchStatus) else str(old_status)
        branch_status_current.labels(status=normalized_old_status).dec()
    branch_status_current.labels(status=normalized_new_status).inc()


def record_incident_created() -> None:
    incident_created_total.inc()
    active_incidents.inc()


def record_incident_resolved() -> None:
    active_incidents.dec()


async def refresh_active_incidents(session: AsyncSession) -> None:
    result = await session.execute(select(func.count(Incident.id)).where(Incident.resolved_at.is_(None)))
    active_incidents.set(int(result.scalar_one() or 0))


async def refresh_branch_status_labels(session: AsyncSession) -> None:
    result = await session.execute(select(Branch.status, func.count(Branch.id)).group_by(Branch.status))
    rows = result.all()
    current_counts = {status.value: 0 for status in BranchStatus}
    for status, count in rows:
        current_counts[str(status)] = int(count)

    for status, count in current_counts.items():
        branch_status_current.labels(status=status).set(count)