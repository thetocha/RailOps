"""Date-bounded ORM reads for analytics. Callers must pass a validated period."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from django.db.models import Count

from apps.analytics.periods import period_bounds
from apps.incidents.models import Incident
from apps.timetables.models import Delay, TrainService


def fetch_incident_records(*, start: date, end: date) -> list[dict[str, object]]:
    start_dt, end_dt = period_bounds(start=start, end=end)
    rows = (
        Incident.objects.filter(reported_at__gte=start_dt, reported_at__lt=end_dt)
        .select_related("station")
        .values("status", "severity", "category", "reported_at", "resolved_at", "station__code")
    )
    return [
        {
            "status": row["status"],
            "severity": row["severity"],
            "category": row["category"],
            "station_code": row["station__code"],
            "reported_at": row["reported_at"],
            "resolved_at": row["resolved_at"],
        }
        for row in rows
    ]


def fetch_delay_records(*, start: date, end: date) -> list[dict[str, object]]:
    rows = (
        Delay.objects.filter(
            train_service__service_date__gte=start,
            train_service__service_date__lte=end,
        )
        .select_related("train_service", "scheduled_stop__station")
        .values(
            "train_service_id",
            "train_service__service_date",
            "kind",
            "delay_seconds",
            "scheduled_stop__station__code",
        )
    )
    return [
        {
            "service_id": _service_id(row["train_service_id"]),
            "service_date": row["train_service__service_date"],
            "kind": row["kind"],
            "delay_seconds": row["delay_seconds"],
            "station_code": row["scheduled_stop__station__code"],
        }
        for row in rows
    ]


def count_train_services(*, start: date, end: date) -> int:
    return TrainService.objects.filter(service_date__gte=start, service_date__lte=end).count()


def count_incidents_by_status(*, start: date, end: date) -> dict[str, int]:
    """ORM totals for routine dashboard cards. Not a Pandas substitute for medians."""
    start_dt, end_dt = period_bounds(start=start, end=end)
    rows = (
        Incident.objects.filter(reported_at__gte=start_dt, reported_at__lt=end_dt)
        .values("status")
        .annotate(total=Count("id"))
    )
    return {str(row["status"]): int(row["total"]) for row in rows}


def _service_id(value: Any) -> str:
    if isinstance(value, UUID):
        return str(value)
    return str(value)
