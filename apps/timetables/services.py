"""Persist normalised timetable records. Callers must not pass request objects."""

from __future__ import annotations

from datetime import date, datetime

from django.db import transaction

from apps.infrastructure.models import Station
from apps.timetables.delays import delay_seconds, measured_event
from apps.timetables.models import Delay, ScheduledStop, TrainService


@transaction.atomic
def upsert_train_service(
    *,
    external_id: str,
    train_number: str,
    origin: Station,
    destination: Station,
    service_date: date,
    source: TrainService.Source,
) -> tuple[TrainService, bool]:
    service, created = TrainService.objects.update_or_create(
        external_id=external_id,
        service_date=service_date,
        defaults={
            "train_number": train_number,
            "origin": origin,
            "destination": destination,
            "source": source,
        },
    )
    return service, created


@transaction.atomic
def upsert_scheduled_stop(
    *,
    train_service: TrainService,
    station: Station,
    stop_sequence: int,
    scheduled_arrival: datetime | None,
    scheduled_departure: datetime | None,
    actual_arrival: datetime | None,
    actual_departure: datetime | None,
) -> tuple[ScheduledStop, bool]:
    stop, created = ScheduledStop.objects.update_or_create(
        train_service=train_service,
        stop_sequence=stop_sequence,
        defaults={
            "station": station,
            "scheduled_arrival": scheduled_arrival,
            "scheduled_departure": scheduled_departure,
            "actual_arrival": actual_arrival,
            "actual_departure": actual_departure,
        },
    )
    refresh_delay_for_stop(stop)
    return stop, created


def refresh_delay_for_stop(stop: ScheduledStop) -> Delay | None:
    measured = measured_event(stop)
    if measured is None:
        Delay.objects.filter(scheduled_stop=stop).delete()
        return None
    kind, scheduled, actual = measured
    seconds = delay_seconds(scheduled=scheduled, actual=actual)
    delay, _created = Delay.objects.update_or_create(
        scheduled_stop=stop,
        kind=kind,
        defaults={
            "train_service": stop.train_service,
            "delay_seconds": seconds,
            "source": Delay.Source.CALCULATED,
        },
    )
    # MVP stores one measured event per stop; drop the other kind if it lingered.
    Delay.objects.filter(scheduled_stop=stop).exclude(kind=kind).delete()
    return delay
