"""Analytics orchestration. Views pass dates; this module returns typed metrics."""

from __future__ import annotations

from datetime import date

from apps.analytics.metrics import calculate_delay_metrics, calculate_incident_metrics
from apps.analytics.periods import default_reporting_period, validate_reporting_period
from apps.analytics.queries import count_train_services, fetch_delay_records, fetch_incident_records
from apps.analytics.schemas import OverviewMetrics
from apps.timetables.models import ON_TIME_THRESHOLD_SECONDS


def build_overview(
    *,
    period_start: date | None = None,
    period_end: date | None = None,
) -> OverviewMetrics:
    if period_start is None or period_end is None:
        period_start, period_end = default_reporting_period()
    period_start, period_end = validate_reporting_period(start=period_start, end=period_end)
    incidents = calculate_incident_metrics(
        fetch_incident_records(start=period_start, end=period_end)
    )
    delays = calculate_delay_metrics(
        fetch_delay_records(start=period_start, end=period_end),
        total_services=count_train_services(start=period_start, end=period_end),
        on_time_threshold_seconds=ON_TIME_THRESHOLD_SECONDS,
    )
    return OverviewMetrics(
        period_start=period_start,
        period_end=period_end,
        incidents=incidents,
        delays=delays,
    )
