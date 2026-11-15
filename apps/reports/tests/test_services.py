from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import User
from apps.analytics.schemas import DelayMetrics, IncidentMetrics, OverviewMetrics
from apps.reports.models import Report
from apps.reports.periods import MAX_MONTHLY_REPORT_DAYS
from apps.reports.services import generate_monthly_operations_report, get_downloadable_report
from apps.timetables.models import ON_TIME_THRESHOLD_SECONDS

pytestmark = pytest.mark.django_db


def test_generate_writes_pdf_under_uuid_path(administrator: User, isolated_media: Path) -> None:
    report = generate_monthly_operations_report(
        actor=administrator,
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
    )
    assert report.status == Report.Status.SUCCESS
    assert report.file.name == f"reports/{report.pk}.pdf"
    assert report.generated_at is not None
    assert report.error_summary == ""
    stored = isolated_media / report.file.name
    assert stored.is_file()
    with report.file.open("rb") as handle:
        payload = handle.read()
    assert payload.startswith(b"%PDF-")
    assert ".." not in report.file.name


def test_generate_records_generic_failure(
    administrator: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*, html: str, stylesheet: str) -> bytes:
        raise RuntimeError("secret-internal-error")

    monkeypatch.setattr("apps.reports.services.render_pdf", boom)
    report = generate_monthly_operations_report(
        actor=administrator,
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
    )
    assert report.status == Report.Status.FAILED
    assert report.error_summary == "PDF generation failed."
    assert "secret-internal-error" not in report.error_summary
    assert not report.file
    assert report.generated_at is None


def test_logging_failure_does_not_mark_success_as_failed(
    administrator: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("log boom")

    monkeypatch.setattr("apps.reports.services.logger.info", boom)
    report = generate_monthly_operations_report(
        actor=administrator,
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
    )
    assert report.status == Report.Status.SUCCESS
    assert report.file
    assert report.error_summary == ""


def test_generate_rejects_dispatcher(dispatcher: User) -> None:
    with pytest.raises(PermissionDenied):
        generate_monthly_operations_report(
            actor=dispatcher,
            period_start=date(2026, 11, 1),
            period_end=date(2026, 11, 15),
        )
    assert Report.objects.count() == 0


def test_generate_rejects_oversized_period_before_persisting(administrator: User) -> None:
    start = date(2026, 1, 1)
    end = start + timedelta(days=MAX_MONTHLY_REPORT_DAYS)
    with pytest.raises(ValidationError):
        generate_monthly_operations_report(actor=administrator, period_start=start, period_end=end)
    assert Report.objects.count() == 0


def test_download_requires_success_and_file(administrator: User) -> None:
    report = Report.objects.create(
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
        requested_by=administrator,
        status=Report.Status.PENDING,
    )
    with pytest.raises(ValidationError, match="not available"):
        get_downloadable_report(actor=administrator, report_id=report.pk)


def test_download_missing_report(administrator: User) -> None:
    with pytest.raises(ValidationError, match="not found"):
        get_downloadable_report(actor=administrator, report_id=uuid4())


def test_download_rejects_viewer(administrator: User, viewer: User) -> None:
    report = generate_monthly_operations_report(
        actor=administrator,
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
    )
    with pytest.raises(PermissionDenied):
        get_downloadable_report(actor=viewer, report_id=report.pk)


def test_monthly_template_includes_empty_states() -> None:
    html = render_to_string(
        "reports/monthly_operations.html",
        {
            "overview": OverviewMetrics(
                period_start=date(2026, 11, 1),
                period_end=date(2026, 11, 15),
                incidents=IncidentMetrics.empty(),
                delays=DelayMetrics.empty(on_time_threshold_seconds=ON_TIME_THRESHOLD_SECONDS),
            ),
            "generated_at": timezone.now(),
            "on_time_threshold_seconds": ON_TIME_THRESHOLD_SECONDS,
            "requested_by": "reports_admin",
        },
    )
    assert "Monthly railway operations report" in html
    assert "No incidents in this period." in html
    assert "n/a (no measured actual times)" in html
    assert str(ON_TIME_THRESHOLD_SECONDS) in html
