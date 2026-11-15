"""Read queries for train services."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from django.db.models import QuerySet

from apps.timetables.models import ScheduledStop, TrainService


def train_service_directory(
    *,
    service_date: date | None = None,
    station_id: UUID | None = None,
    train_number: str = "",
) -> QuerySet[TrainService]:
    queryset = TrainService.objects.select_related("origin", "destination")
    if service_date is not None:
        queryset = queryset.filter(service_date=service_date)
    if station_id is not None:
        queryset = queryset.filter(stops__station_id=station_id).distinct()
    term = train_number.strip()
    if term:
        queryset = queryset.filter(train_number__icontains=term)
    return queryset.order_by("-service_date", "train_number")


def stops_for_service(service: TrainService) -> QuerySet[ScheduledStop]:
    return (
        service.stops.select_related("station")
        .prefetch_related("delay_records")
        .order_by("stop_sequence")
    )
