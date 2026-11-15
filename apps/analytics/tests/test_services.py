from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from apps.accounts.models import User
from apps.analytics.queries import count_incidents_by_status
from apps.analytics.services import build_overview
from apps.incidents.models import Incident
from apps.incidents.services import create_incident, transition_incident
from apps.infrastructure.models import Station
from apps.timetables.models import TrainService
from apps.timetables.services import upsert_scheduled_stop, upsert_train_service

pytestmark = pytest.mark.django_db


def test_overview_uses_persisted_incidents_and_ignores_other_periods(
    dispatcher: User,
    berlin: Station,
    hamburg: Station,
) -> None:
    inside = create_incident(
        actor=dispatcher,
        title="Inside period",
        description="Counted.",
        station=berlin,
        category=Incident.Category.SIGNAL_FAILURE,
        severity=Incident.Severity.HIGH,
    )
    outside = create_incident(
        actor=dispatcher,
        title="Outside period",
        description="Not counted.",
        station=hamburg,
        category=Incident.Category.WEATHER,
        severity=Incident.Severity.LOW,
    )
    reported = datetime(2026, 7, 10, 8, 0, tzinfo=UTC)
    Incident.objects.filter(pk=inside.pk).update(
        reported_at=reported,
        status=Incident.Status.RESOLVED,
        resolved_at=reported + timedelta(hours=2),
    )
    Incident.objects.filter(pk=outside.pk).update(
        reported_at=datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
    )
    overview = build_overview(period_start=date(2026, 7, 1), period_end=date(2026, 7, 31))
    assert overview.incidents.total == 1
    assert overview.incidents.resolved_count == 1
    assert overview.incidents.average_resolution_seconds == 2 * 3600
    assert overview.delays.total_services == 0
    counts = count_incidents_by_status(start=date(2026, 7, 1), end=date(2026, 7, 31))
    assert counts[Incident.Status.RESOLVED] == 1


def test_delay_overview_excludes_services_without_actuals(
    berlin: Station,
    hamburg: Station,
) -> None:
    day = date(2026, 8, 15)
    scheduled = datetime(2026, 8, 15, 8, 0, tzinfo=UTC)
    late, _ = upsert_train_service(
        external_id="ICE-1",
        train_number="ICE 1",
        origin=berlin,
        destination=hamburg,
        service_date=day,
        source=TrainService.Source.MOCK,
    )
    missing, _ = upsert_train_service(
        external_id="RE-2",
        train_number="RE 2",
        origin=berlin,
        destination=hamburg,
        service_date=day,
        source=TrainService.Source.MOCK,
    )
    upsert_scheduled_stop(
        train_service=late,
        station=hamburg,
        stop_sequence=1,
        scheduled_arrival=scheduled,
        scheduled_departure=None,
        actual_arrival=scheduled + timedelta(minutes=12),
        actual_departure=None,
    )
    upsert_scheduled_stop(
        train_service=missing,
        station=hamburg,
        stop_sequence=1,
        scheduled_arrival=scheduled,
        scheduled_departure=None,
        actual_arrival=None,
        actual_departure=None,
    )
    overview = build_overview(period_start=day, period_end=day)
    assert overview.delays.total_services == 2
    assert overview.delays.measured_services == 1
    assert overview.delays.delayed_services == 1
    assert overview.delays.on_time_percentage == 0.0
    assert overview.delays.maximum_delay_seconds == 12 * 60
    assert overview.delays.by_station[0].station_code == "HH"


def test_unresolved_open_incident_does_not_invent_resolution_time(
    dispatcher: User,
    berlin: Station,
) -> None:
    incident = create_incident(
        actor=dispatcher,
        title="Still open",
        description="No resolution yet.",
        station=berlin,
        category=Incident.Category.OTHER,
        severity=Incident.Severity.MEDIUM,
    )
    transition_incident(
        incident_id=incident.pk,
        new_status=Incident.Status.IN_PROGRESS,
        actor=dispatcher,
    )
    Incident.objects.filter(pk=incident.pk).update(
        reported_at=datetime(2026, 9, 1, 9, 0, tzinfo=UTC),
    )
    overview = build_overview(period_start=date(2026, 9, 1), period_end=date(2026, 9, 1))
    assert overview.incidents.total == 1
    assert overview.incidents.open_count == 1
    assert overview.incidents.resolved_count == 0
    assert overview.incidents.average_resolution_seconds is None
    assert overview.incidents.median_resolution_seconds is None
