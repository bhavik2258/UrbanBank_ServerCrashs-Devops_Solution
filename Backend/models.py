from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class BranchStatus(str, Enum):
    healthy = "healthy"
    warning = "warning"
    critical = "critical"


class AlertType(str, Enum):
    service_down = "service_down"
    high_cpu = "high_cpu"
    disk_full = "disk_full"


class AlertSeverity(str, Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[BranchStatus] = mapped_column(
        String(20), nullable=False, default=BranchStatus.healthy.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    metrics: Mapped[list["Metric"]] = relationship(
        back_populates="branch", cascade="all, delete-orphan", lazy="selectin"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="branch", cascade="all, delete-orphan", lazy="selectin"
    )
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="branch", cascade="all, delete-orphan", lazy="selectin"
    )


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cpu_usage: Mapped[float] = mapped_column(Float, nullable=False)
    ram_usage: Mapped[float] = mapped_column(Float, nullable=False)
    disk_usage: Mapped[float] = mapped_column(Float, nullable=False)
    core_banking_service_up: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    postgres_db_up: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    network_up: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    branch: Mapped["Branch"] = relationship(back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_type: Mapped[AlertType] = mapped_column(String(30), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(String(20), nullable=False, index=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    fired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    branch: Mapped["Branch"] = relationship(back_populates="alerts")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="alert")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    auto_healed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    heal_action: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)

    branch: Mapped["Branch"] = relationship(back_populates="incidents")
    alert: Mapped["Alert | None"] = relationship(back_populates="incidents")
