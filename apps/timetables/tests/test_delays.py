from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.gis.geos import Point
from django.db import IntegrityError, transaction

from apps.infrastructure.models import Station
from apps.timetables.delays import delay_seconds, format_delay_seconds, measured_event
from apps.timetables.models import Delay, ScheduledStop, TrainService
from apps.timetables.services import (
    refresh_delay_for_stop,
    upsert_scheduled_stop,
    upsert_train_service,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def stations(db: None) -> tuple[Station, Station]:
    origin = Station.objects.create(
        name="Berlin Hauptbahnhof",
        code="BHF",
        city="Berlin",
        location=Point(13.3695, 52.5255, srid=4326),
    )
    destination = Station.objects.create(
        name="Hamburg Hauptbahnhof",
        code="HH",
        city="Hamburg",
        location=Point(10.0069, 53.5528, srid=4326),
    )
    return origin, destination


def test_delay_seconds_is_signed() -> None:
    scheduled = datetime(2026, 11, 15, 8, 0, tzinfo=UTC)
    late = scheduled + timedelta(minutes=4)
    early = scheduled - timedelta(minutes=1)
    assert delay_seconds(scheduled=scheduled, actual=late) == 240
    assert delay_seconds(scheduled=scheduled, actual=early) == -60


def test_missing_actuals_do_not_create_delay(
    stations: tuple[Station, Station],
) -> None:
    origin, destination = stations
    service, _ = upsert_train_service(
        external_id="T1",
        train_number="ICE 1",
        origin=origin,
        destination=destination,
        service_date=datetime(2026, 11, 15, tzinfo=UTC).date(),
        source=TrainService.Source.MOCK,
    )
    stop, _ = upsert_scheduled_stop(
        train_service=service,
        station=destination,
        stop_sequence=1,
        scheduled_arrival=datetime(2026, 11, 15, 8, 0, tzinfo=UTC),
        scheduled_departure=None,
        actual_arrival=None,
        actual_departure=None,
    )
    assert refresh_delay_for_stop(stop) is None
    assert not Delay.objects.filter(scheduled_stop=stop).exists()
    assert measured_event(stop) is None


def test_overnight_arrival_uses_calendar_datetimes(
    stations: tuple[Station, Station],
) -> None:
    origin, destination = stations
    service, _ = upsert_train_service(
        external_id="T2",
        train_number="NJ 1",
        origin=origin,
        destination=destination,
        service_date=datetime(2026, 11, 15, tzinfo=UTC).date(),
        source=TrainService.Source.MOCK,
    )
    stop, _ = upsert_scheduled_stop(
        train_service=service,
        station=destination,
        stop_sequence=2,
        scheduled_arrival=datetime(2026, 11, 16, 0, 10, tzinfo=UTC),
        scheduled_departure=None,
        actual_arrival=datetime(2026, 11, 16, 0, 25, tzinfo=UTC),
        actual_departure=None,
    )
    delay = refresh_delay_for_stop(stop)
    assert delay is not None
    assert delay.kind == Delay.Kind.ARRIVAL
    assert delay.delay_seconds == 900


def test_format_delay_seconds_uses_minutes() -> None:
    assert format_delay_seconds(600) == "10 min"
    assert format_delay_seconds(-45) == "-45 s"
    assert format_delay_seconds(90) == "1 min 30 s"


def test_external_id_and_service_date_are_unique(
    stations: tuple[Station, Station],
) -> None:
    origin, destination = stations
    upsert_train_service(
        external_id="T-UNIQUE",
        train_number="ICE 1",
        origin=origin,
        destination=destination,
        service_date=datetime(2026, 11, 15, tzinfo=UTC).date(),
        source=TrainService.Source.MOCK,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        TrainService.objects.create(
            external_id="T-UNIQUE",
            train_number="ICE 2",
            origin=origin,
            destination=destination,
            service_date=datetime(2026, 11, 15, tzinfo=UTC).date(),
            source=TrainService.Source.CSV,
        )


def test_stop_sequence_is_unique_per_service(
    stations: tuple[Station, Station],
) -> None:
    origin, destination = stations
    service, _ = upsert_train_service(
        external_id="T-SEQ",
        train_number="RE 1",
        origin=origin,
        destination=destination,
        service_date=datetime(2026, 11, 15, tzinfo=UTC).date(),
        source=TrainService.Source.MOCK,
    )
    upsert_scheduled_stop(
        train_service=service,
        station=origin,
        stop_sequence=1,
        scheduled_arrival=None,
        scheduled_departure=datetime(2026, 11, 15, 8, 0, tzinfo=UTC),
        actual_arrival=None,
        actual_departure=None,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        ScheduledStop.objects.create(
            train_service=service,
            station=destination,
            stop_sequence=1,
            scheduled_arrival=datetime(2026, 11, 15, 9, 0, tzinfo=UTC),
        )
