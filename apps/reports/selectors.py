"""Read queries for reports."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.reports.models import Report


def report_directory() -> QuerySet[Report]:
    return Report.objects.select_related("requested_by").order_by("-created_at")
