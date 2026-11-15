"""Report generation. Views must not render PDFs themselves."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.permissions import require_authenticated_user
from apps.analytics.services import build_overview
from apps.reports.models import Report
from apps.reports.pdf import render_pdf
from apps.reports.periods import validate_monthly_period
from apps.reports.permissions import PERM_ADD_REPORT, PERM_VIEW_REPORT
from apps.timetables.models import ON_TIME_THRESHOLD_SECONDS

logger = logging.getLogger(__name__)

_STYLESHEET = Path(__file__).resolve().parent / "static" / "monthly_operations.css"


def generate_monthly_operations_report(
    *,
    actor: User,
    period_start: date,
    period_end: date,
) -> Report:
    actor = require_authenticated_user(actor)
    if not actor.has_perm(PERM_ADD_REPORT):
        raise PermissionDenied
    period_start, period_end = validate_monthly_period(start=period_start, end=period_end)
    report = Report.objects.create(
        report_type=Report.ReportType.MONTHLY_OPERATIONS,
        period_start=period_start,
        period_end=period_end,
        requested_by=actor,
        status=Report.Status.PENDING,
    )
    try:
        overview = build_overview(period_start=period_start, period_end=period_end)
        html = render_to_string(
            "reports/monthly_operations.html",
            {
                "overview": overview,
                "generated_at": timezone.now(),
                "on_time_threshold_seconds": ON_TIME_THRESHOLD_SECONDS,
                "requested_by": actor.get_username(),
            },
        )
        pdf_bytes = render_pdf(html=html, stylesheet=_STYLESHEET.read_text(encoding="utf-8"))
        report.file.save(f"{report.pk}.pdf", ContentFile(pdf_bytes), save=False)
        report.status = Report.Status.SUCCESS
        report.generated_at = timezone.now()
        report.error_summary = ""
        report.save(update_fields=["file", "status", "generated_at", "error_summary"])
        logger.info(
            "Generated report id=%s period=%s..%s actor=%s bytes=%s",
            report.pk,
            period_start,
            period_end,
            actor.username,
            report.file.size,
        )
    except Exception:
        logger.exception("Failed to generate report id=%s", report.pk)
        report.status = Report.Status.FAILED
        report.error_summary = "PDF generation failed."
        report.save(update_fields=["status", "error_summary"])
    return report


def get_downloadable_report(*, actor: User, report_id: UUID | str) -> Report:
    actor = require_authenticated_user(actor)
    if not actor.has_perm(PERM_VIEW_REPORT):
        raise PermissionDenied
    try:
        report = Report.objects.get(pk=report_id)
    except (Report.DoesNotExist, ValidationError, ValueError) as exc:
        raise ValidationError("Report not found.") from exc
    if report.status != Report.Status.SUCCESS or not report.file:
        raise ValidationError("This report is not available for download.")
    return report
