from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.base import ModelBase

from apps.infrastructure.models import RailwayLine, Station


class Incident(models.Model):
    class Category(models.TextChoices):
        INFRASTRUCTURE = "infrastructure", "Infrastructure"
        TECHNICAL_FAILURE = "technical_failure", "Technical failure"
        SIGNAL_FAILURE = "signal_failure", "Signal failure"
        TRACK_OBSTRUCTION = "track_obstruction", "Track obstruction"
        WEATHER = "weather", "Weather"
        OPERATIONAL_DELAY = "operational_delay", "Operational delay"
        OTHER = "other", "Other"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="incidents",
    )
    railway_line = models.ForeignKey(
        RailwayLine,
        on_delete=models.SET_NULL,
        related_name="incidents",
        blank=True,
        null=True,
    )
    category = models.CharField(max_length=32, choices=Category.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_incidents",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_incidents",
        blank=True,
        null=True,
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-reported_at"]
        verbose_name = "incident"
        verbose_name_plural = "incidents"
        indexes = [
            models.Index(fields=["status", "severity"], name="incident_status_severity"),
            models.Index(fields=["station", "-reported_at"], name="incident_station_reported"),
            models.Index(fields=["-reported_at"], name="incident_reported_at"),
            models.Index(fields=["assigned_to"], name="incident_assigned_to"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""),
                name="incident_title_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(resolved_at__isnull=True)
                | models.Q(status__in=["resolved", "closed"]),
                name="incident_resolved_at_matches_status",
            ),
        ]
        permissions = [
            ("reopen_closed_incident", "Can reopen a closed incident"),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"


class IncidentEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        STATUS_CHANGED = "status_changed", "Status changed"
        SEVERITY_CHANGED = "severity_changed", "Severity changed"
        ASSIGNED = "assigned", "Assigned"
        RESOLVED = "resolved", "Resolved"
        COMMENT = "comment", "Comment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="incident_events",
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    previous_status = models.CharField(
        max_length=16,
        choices=Incident.Status.choices,
        blank=True,
        null=True,
    )
    new_status = models.CharField(
        max_length=16,
        choices=Incident.Status.choices,
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "incident event"
        verbose_name_plural = "incident events"

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} @ {self.created_at}"

    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        if not self._state.adding:
            raise ValidationError("Incident events are immutable.")
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def delete(
        self,
        using: str | None = None,
        keep_parents: bool = False,
    ) -> NoReturn:
        raise ValidationError("Incident events are immutable.")
