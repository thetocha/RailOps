"""Reporting-period validation. Bounds memory used by analytics queries."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

MAX_REPORTING_DAYS = 366
DEFAULT_REPORTING_DAYS = 30


def default_reporting_period(*, today: date | None = None) -> tuple[date, date]:
    end = today or timezone.localdate()
    start = end - timedelta(days=DEFAULT_REPORTING_DAYS - 1)
    return start, end


def validate_reporting_period(*, start: date, end: date) -> tuple[date, date]:
    if start > end:
        raise ValidationError({"period_start": "Start date must be on or before the end date."})
    span = (end - start).days + 1
    if span > MAX_REPORTING_DAYS:
        raise ValidationError(
            {"period_end": f"Reporting period cannot exceed {MAX_REPORTING_DAYS} days."}
        )
    return start, end


def period_bounds(*, start: date, end: date) -> tuple[datetime, datetime]:
    """Inclusive calendar dates as a half-open datetime window in the current timezone."""
    start, end = validate_reporting_period(start=start, end=end)
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, time.min), tz)
    end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min), tz)
    return start_dt, end_dt
