from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from apps.analytics.metrics import calculate_delay_metrics, calculate_incident_metrics
from apps.incidents.models import Incident
from apps.timetables.models import ON_TIME_THRESHOLD_SECONDS, Delay


def test_empty_incident_records_return_zeros() -> None:
    metrics = calculate_incident_metrics([])
    assert metrics.total == 0
    assert metrics.open_count == 0
    assert metrics.resolved_count == 0
    assert metrics.average_resolution_seconds is None
    assert metrics.median_resolution_seconds is None
    assert metrics.by_severity == ()
    assert metrics.volume_by_month == ()


def test_unresolved_incidents_are_excluded_from_resolution_time() -> None:
    reported = datetime(2026, 3, 1, 10, 0, tzinfo=UTC)
    records: list[dict[str, object]] = [
        {
            "status": Incident.Status.OPEN,
            "severity": Incident.Severity.HIGH,
            "category": Incident.Category.SIGNAL_FAILURE,
            "station_code": "BHF",
            "reported_at": reported,
            "resolved_at": None,
        },
        {
            "status": Incident.Status.RESOLVED,
            "severity": Incident.Severity.LOW,
            "category": Incident.Category.WEATHER,
            "station_code": "HH",
            "reported_at": reported,
            "resolved_at": reported.replace(hour=12),
        },
        {
            "status": Incident.Status.CLOSED,
            "severity": Incident.Severity.LOW,
            "category": Incident.Category.WEATHER,
            "station_code": "HH",
            "reported_at": reported,
            "resolved_at": reported.replace(hour=14),
        },
    ]
    metrics = calculate_incident_metrics(records)
    assert metrics.total == 3
    assert metrics.open_count == 1
    assert metrics.resolved_count == 2
    assert metrics.average_resolution_seconds == 3 * 3600
    assert metrics.median_resolution_seconds == 3 * 3600
    assert metrics.per_station[0].key == "HH"
    assert metrics.per_station[0].count == 2
    by_severity = {item.key: item.count for item in metrics.by_severity}
    assert by_severity[Incident.Severity.HIGH] == 1
    assert by_severity[Incident.Severity.CRITICAL] == 0
    assert metrics.volume_by_month[0].key == "2026-03"


def test_invalid_and_negative_resolution_times_are_ignored() -> None:
    reported = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)
    records: list[dict[str, object]] = [
        {
            "status": Incident.Status.RESOLVED,
            "severity": Incident.Severity.MEDIUM,
            "category": Incident.Category.OTHER,
            "station_code": "BHF",
            "reported_at": reported,
            "resolved_at": "not-a-date",
        },
        {
            "status": Incident.Status.RESOLVED,
            "severity": Incident.Severity.MEDIUM,
            "category": Incident.Category.OTHER,
            "station_code": "BHF",
            "reported_at": reported,
            "resolved_at": reported.replace(hour=8),
        },
        {
            "status": Incident.Status.RESOLVED,
            "severity": Incident.Severity.MEDIUM,
            "category": Incident.Category.OTHER,
            "station_code": "BHF",
            "reported_at": reported,
            "resolved_at": reported.replace(hour=11),
        },
    ]
    metrics = calculate_incident_metrics(records)
    assert metrics.total == 3
    assert metrics.average_resolution_seconds == 3600
    assert metrics.median_resolution_seconds == 3600


def test_delay_metrics_exclude_unmeasured_and_use_arrival_when_both_exist() -> None:
    records: list[dict[str, object]] = [
        {
            "service_id": "late",
            "service_date": date(2026, 5, 1),
            "kind": Delay.Kind.ARRIVAL,
            "delay_seconds": 600,
            "station_code": "HH",
        },
        {
            "service_id": "late",
            "service_date": date(2026, 5, 1),
            "kind": Delay.Kind.DEPARTURE,
            "delay_seconds": 60,
            "station_code": "BHF",
        },
        {
            "service_id": "early",
            "service_date": date(2026, 5, 1),
            "kind": Delay.Kind.ARRIVAL,
            "delay_seconds": -30,
            "station_code": "BHF",
        },
        {
            "service_id": "ontime",
            "service_date": date(2026, 5, 2),
            "kind": Delay.Kind.DEPARTURE,
            "delay_seconds": 120,
            "station_code": "BHF",
        },
    ]
    metrics = calculate_delay_metrics(records, total_services=5)
    assert metrics.total_services == 5
    assert metrics.measured_services == 3
    assert metrics.delayed_services == 1
    assert metrics.maximum_delay_seconds == 600
    assert metrics.median_delay_seconds == 120
    assert metrics.average_delay_seconds == (600 + -30 + 120) / 3
    assert metrics.on_time_percentage == pytest.approx((2 / 3) * 100)
    assert metrics.on_time_threshold_seconds == ON_TIME_THRESHOLD_SECONDS
    assert metrics.by_station[0].station_code == "HH"
    assert metrics.by_station[0].average_delay_seconds == 600
    days = {item.day: item for item in metrics.by_day}
    assert days[date(2026, 5, 1)].delayed_count == 1
    assert days[date(2026, 5, 1)].measured_count == 2


def test_unmeasured_services_are_not_treated_as_on_time() -> None:
    metrics = calculate_delay_metrics([], total_services=4)
    assert metrics.total_services == 4
    assert metrics.measured_services == 0
    assert metrics.delayed_services == 0
    assert metrics.on_time_percentage is None
    assert metrics.average_delay_seconds is None


def test_outlier_delay_does_not_become_a_zero() -> None:
    records: list[dict[str, object]] = [
        {
            "service_id": "a",
            "service_date": date(2026, 6, 1),
            "kind": Delay.Kind.ARRIVAL,
            "delay_seconds": 30,
            "station_code": "BHF",
        },
        {
            "service_id": "b",
            "service_date": date(2026, 6, 1),
            "kind": Delay.Kind.ARRIVAL,
            "delay_seconds": 10_800,
            "station_code": "BHF",
        },
        {
            "service_id": "c",
            "service_date": date(2026, 6, 1),
            "kind": Delay.Kind.ARRIVAL,
            "delay_seconds": 60,
            "station_code": "BHF",
        },
    ]
    metrics = calculate_delay_metrics(records, total_services=3)
    assert metrics.median_delay_seconds == 60
    assert metrics.maximum_delay_seconds == 10_800
    assert metrics.delayed_services == 1
