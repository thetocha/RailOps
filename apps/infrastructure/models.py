from __future__ import annotations

import uuid

from django.contrib.gis.db import models


class Station(models.Model):
    """Railway station with a unique code and WGS84 location."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32)
    city = models.CharField(max_length=128)
    location = models.PointField(srid=4326, geography=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "station"
        verbose_name_plural = "stations"
        indexes = [
            models.Index(fields=["is_active", "name"], name="infra_station_active_name"),
        ]
        constraints = [
            models.UniqueConstraint(fields=("code",), name="infra_station_code_unique"),
            models.CheckConstraint(
                condition=~models.Q(code=""),
                name="infra_station_code_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="infra_station_name_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(city=""),
                name="infra_station_city_not_empty",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def latitude(self) -> float:
        return float(self.location.y)

    @property
    def longitude(self) -> float:
        return float(self.location.x)


class RailwayLine(models.Model):
    """Named corridor between two stations. Geometry is stored, never inferred."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32)
    start_station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="lines_starting",
    )
    end_station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="lines_ending",
    )
    geometry = models.LineStringField(srid=4326, geography=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "railway line"
        verbose_name_plural = "railway lines"
        indexes = [
            models.Index(fields=["is_active", "name"], name="infra_line_active_name"),
        ]
        constraints = [
            models.UniqueConstraint(fields=("code",), name="infra_line_code_unique"),
            models.CheckConstraint(
                condition=~models.Q(code=""),
                name="infra_line_code_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="infra_line_name_not_empty",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
