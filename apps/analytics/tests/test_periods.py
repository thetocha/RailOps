from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError

from apps.analytics.periods import (
    MAX_REPORTING_DAYS,
    default_reporting_period,
    period_bounds,
    validate_reporting_period,
)


def test_start_after_end_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_reporting_period(start=date(2026, 2, 2), end=date(2026, 2, 1))
    assert "period_start" in exc.value.message_dict


def test_period_longer_than_max_is_rejected() -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=MAX_REPORTING_DAYS)
    with pytest.raises(ValidationError) as exc:
        validate_reporting_period(start=start, end=end)
    assert "period_end" in exc.value.message_dict


def test_max_inclusive_span_is_allowed() -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=MAX_REPORTING_DAYS - 1)
    assert validate_reporting_period(start=start, end=end) == (start, end)


def test_period_bounds_are_half_open() -> None:
    start_dt, end_dt = period_bounds(start=date(2026, 3, 1), end=date(2026, 3, 1))
    assert start_dt.date() == date(2026, 3, 1)
    assert end_dt.date() == date(2026, 3, 2)
    assert start_dt.tzinfo is not None
    assert end_dt.tzinfo is not None


def test_default_period_is_thirty_days_ending_today() -> None:
    start, end = default_reporting_period(today=date(2026, 6, 30))
    assert end == date(2026, 6, 30)
    assert start == date(2026, 6, 1)
