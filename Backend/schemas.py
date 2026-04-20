from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from models import AlertSeverity, AlertType, BranchStatus


class MetricBase(BaseModel):
    cpu_usage: float = Field(ge=0, le=100)
    ram_usage: float = Field(ge=0, le=100)
    disk_usage: float = Field(ge=0, le=100)
    core_banking_service_up: bool
    postgres_db_up: bool
    network_up: bool


class MetricCreate(MetricBase):
    pass


class MetricRead(MetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    recorded_at: datetime


class BranchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    bank_name: str = Field(default="UrbanBank", min_length=2, max_length=120)
    ip_address: str = Field(min_length=7, max_length=45)
    location: str = Field(min_length=2, max_length=120)
    status: BranchStatus = BranchStatus.healthy


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    bank_name: str
    ip_address: str
    location: str
    status: BranchStatus
    created_at: datetime
    uptime_percent: float = Field(default=100.0, ge=0, le=100)
    latest_metric: MetricRead | None = None


class AlertCreate(BaseModel):
    branch_id: int
    alert_type: AlertType
    message: str = Field(min_length=1, max_length=1000)
    severity: AlertSeverity


class AlertResolveResponse(BaseModel):
    message: str
    alert_id: int
    resolved: bool


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    alert_type: AlertType
    message: str
    severity: AlertSeverity
    is_resolved: bool
    fired_at: datetime
    resolved_at: datetime | None = None


class IncidentCreate(BaseModel):
    branch_id: int
    alert_id: int | None = None
    description: str = Field(min_length=1, max_length=1000)
    auto_healed: bool = False
    heal_action: str = Field(min_length=1, max_length=255)
    started_at: datetime | None = None
    resolved_at: datetime | None = None
    duration_minutes: float | None = None


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    alert_id: int | None = None
    description: str
    auto_healed: bool
    heal_action: str
    started_at: datetime
    resolved_at: datetime | None = None
    duration_minutes: float | None = None


class IncidentPage(BaseModel):
    items: list[IncidentRead]
    total: int
    page: int
    page_size: int


class DashboardSummary(BaseModel):
    total_branches: int
    active_alerts: int
    incidents_today: int
    avg_uptime_percent: float


class AlertVolumeByBranch(BaseModel):
    branch_id: int
    branch_name: str
    critical: int
    warning: int
    info: int
    total: int


class BankOpsKpis(BaseModel):
    transaction_success_rate_percent: float = Field(ge=0, le=100)
    authentication_failures_last_hour: int = Field(ge=0)
    transfer_p95_latency_ms: float = Field(ge=0)
    transfer_error_rate_percent: float = Field(ge=0, le=100)
    atm_pos_network_uptime_percent: float = Field(ge=0, le=100)
    db_replication_lag_seconds: float = Field(ge=0)
    alert_volume_by_branch: list[AlertVolumeByBranch]


class SimulationResponse(BaseModel):
    message: str
    branch_id: int
    branch_status: BranchStatus
    alert_id: int | None = None
    incident_id: int | None = None


class APIMessage(BaseModel):
    message: str


class BranchWithMetrics(BaseModel):
    branch: BranchRead
    metrics_history: list[MetricRead]
