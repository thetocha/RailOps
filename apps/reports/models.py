from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


def report_upload_to(instance: Report, _filename: str) -> str:
    """Store PDFs under media/reports using the report UUID. Ignore caller filenames."""
    return str(Path("reports") / f"{instance.pk}.pdf")


class Report(models.Model):
    class ReportType(models.TextChoices):
        MONTHLY_OPERATIONS = "monthly_operations", "Monthly railway operations"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(
        max_length=32,
        choices=ReportType.choices,
        default=ReportType.MONTHLY_OPERATIONS,
    )
    period_start = models.DateField()
    period_end = models.DateField()
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_reports",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    generated_at = models.DateTimeField(blank=True, null=True)
    file = models.FileField(upload_to=report_upload_to, blank=True)
    error_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "report"
        verbose_name_plural = "reports"
        indexes = [
            models.Index(fields=["-created_at"], name="report_created_at"),
            models.Index(fields=["status"], name="report_status"),
            models.Index(
                fields=["requested_by", "generated_at"], name="report_requested_generated"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(period_end__gte=models.F("period_start")),
                name="report_period_end_on_or_after_start",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_report_type_display()} {self.period_start}–{self.period_end}"
