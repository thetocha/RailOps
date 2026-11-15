from __future__ import annotations

from datetime import date

import pytest
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from apps.accounts.models import User
from apps.reports.models import Report, report_upload_to

pytestmark = pytest.mark.django_db


def test_period_end_before_start_is_rejected(administrator: User) -> None:
    with pytest.raises(IntegrityError):
        Report.objects.create(
            period_start=date(2026, 2, 2),
            period_end=date(2026, 2, 1),
            requested_by=administrator,
        )


def test_upload_to_ignores_caller_filename(administrator: User) -> None:
    report = Report.objects.create(
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
        requested_by=administrator,
    )
    assert report_upload_to(report, "../../etc/passwd") == f"reports/{report.pk}.pdf"
    assert report_upload_to(report, "nested/path/evil.pdf") == f"reports/{report.pk}.pdf"


def test_string_includes_period(administrator: User) -> None:
    report = Report.objects.create(
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
        requested_by=administrator,
    )
    assert str(report) == "Monthly railway operations 2026-11-01–2026-11-15"


def test_requested_by_is_protected(administrator: User) -> None:
    report = Report.objects.create(
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
        requested_by=administrator,
    )
    with pytest.raises(ProtectedError):
        administrator.delete()
    assert Report.objects.filter(pk=report.pk).exists()
