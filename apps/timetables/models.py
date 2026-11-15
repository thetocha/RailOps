from __future__ import annotations

import uuid

from django.db import models

from apps.infrastructure.models import Station

# Services with delay_seconds > this threshold are treated as delayed.
# Missing actual times are excluded, never treated as zero.
ON_TIME_THRESHOLD_SECONDS = 300


class TrainService(models.Model):
    class Source(models.TextChoices):
        MOCK = "mock", "Mock provider"
        CSV = "csv", "CSV import"
        HTTP = "http", "HTTP provider"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=64)
    train_number = models.CharField(max_length=32)
    origin = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="originating_services",
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="terminating_services",
    )
    service_date = models.DateField()
    source = models.CharField(max_length=16, choices=Source.choices)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-service_date", "train_number"]
        verbose_name = "train service"
        verbose_name_plural = "train services"
        indexes = [
            models.Index(fields=["service_date", "train_number"], name="service_date_number"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("external_id", "service_date"),
                name="trainservice_external_id_date_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.train_number} on {self.service_date}"


class ScheduledStop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    train_service = models.ForeignKey(
        TrainService,
        on_delete=models.CASCADE,
        related_name="stops",
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="scheduled_stops",
    )
    stop_sequence = models.PositiveIntegerField()
    scheduled_arrival = models.DateTimeField(blank=True, null=True)
    scheduled_departure = models.DateTimeField(blank=True, null=True)
    actual_arrival = models.DateTimeField(blank=True, null=True)
    actual_departure = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["stop_sequence"]
        verbose_name = "scheduled stop"
        verbose_name_plural = "scheduled stops"
        constraints = [
            models.UniqueConstraint(
                fields=("train_service", "stop_sequence"),
                name="scheduledstop_service_sequence_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(stop_sequence__gte=1),
                name="scheduledstop_sequence_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.train_service.train_number} #{self.stop_sequence} {self.station.code}"


class Delay(models.Model):
    class Kind(models.TextChoices):
        ARRIVAL = "arrival", "Arrival"
        DEPARTURE = "departure", "Departure"

    class Source(models.TextChoices):
        CALCULATED = "calculated", "Calculated"
        IMPORT = "import", "Import"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    train_service = models.ForeignKey(
        TrainService,
        on_delete=models.CASCADE,
        related_name="delays",
    )
    scheduled_stop = models.ForeignKey(
        ScheduledStop,
        on_delete=models.CASCADE,
        related_name="delay_records",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    delay_seconds = models.IntegerField()
    recorded_at = models.DateTimeField(auto_now=True)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.CALCULATED)

    class Meta:
        verbose_name = "delay"
        verbose_name_plural = "delays"
        constraints = [
            models.UniqueConstraint(
                fields=("scheduled_stop", "kind"),
                name="delay_stop_kind_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind} {self.delay_seconds}s"
