from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError

from apps.reports.periods import (
    MAX_MONTHLY_REPORT_DAYS,
    default_monthly_period,
    validate_monthly_period,
)


def test_start_after_end_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_monthly_period(start=date(2026, 2, 2), end=date(2026, 2, 1))
    assert "period_start" in exc.value.message_dict


def test_period_longer_than_max_is_rejected() -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=MAX_MONTHLY_REPORT_DAYS)
    with pytest.raises(ValidationError) as exc:
        validate_monthly_period(start=start, end=end)
    assert "period_end" in exc.value.message_dict


def test_max_inclusive_span_is_allowed() -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=MAX_MONTHLY_REPORT_DAYS - 1)
    assert validate_monthly_period(start=start, end=end) == (start, end)


def test_default_period_is_first_of_month_through_today() -> None:
    start, end = default_monthly_period(today=date(2026, 11, 15))
    assert start == date(2026, 11, 1)
    assert end == date(2026, 11, 15)
