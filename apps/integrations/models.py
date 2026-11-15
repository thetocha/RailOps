from __future__ import annotations

import uuid

from django.db import models


class ExternalSyncRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration_name = models.CharField(max_length=64)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)
    records_processed = models.PositiveIntegerField(default=0)
    records_created = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    error_summary = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "external sync run"
        verbose_name_plural = "external sync runs"
        indexes = [
            models.Index(fields=["-started_at"], name="sync_run_started_at"),
        ]
        permissions = [
            ("run_timetable_sync", "Can run timetable synchronization"),
        ]

    def __str__(self) -> str:
        return f"{self.integration_name} {self.status} {self.started_at}"
