"""Monthly report period validation. Stricter than analytics (31 days)."""

from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.utils import timezone

MAX_MONTHLY_REPORT_DAYS = 31


def default_monthly_period(*, today: date | None = None) -> tuple[date, date]:
    end = today or timezone.localdate()
    start = end.replace(day=1)
    return start, end


def validate_monthly_period(*, start: date, end: date) -> tuple[date, date]:
    if start > end:
        raise ValidationError({"period_start": "Start date must be on or before the end date."})
    span = (end - start).days + 1
    if span > MAX_MONTHLY_REPORT_DAYS:
        raise ValidationError(
            {"period_end": f"Monthly reports cannot exceed {MAX_MONTHLY_REPORT_DAYS} days."}
        )
    return start, end
