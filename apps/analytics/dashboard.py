"""Dashboard snapshot. HTML views render this; JavaScript only enhances charts/maps."""

from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from apps.analytics.schemas import OverviewMetrics
from apps.analytics.services import build_overview
from apps.incidents.models import Incident
from apps.incidents.selectors import incident_directory
from apps.infrastructure.selectors import station_directory
from apps.timetables.models import TrainService

RECENT_LIMIT = 8
MAX_MAP_STATIONS = 200


@dataclass(frozen=True)
class ChartSeries:
    labels: tuple[str, ...]
    values: tuple[int, ...]

    def as_json(self) -> dict[str, list[str] | list[int]]:
        return {"labels": list(self.labels), "values": list(self.values)}


@dataclass(frozen=True)
class DashboardSnapshot:
    overview: OverviewMetrics
    critical_incidents: int
    recent_incidents: tuple[Incident, ...]
    recent_services: tuple[TrainService, ...]
    station_markers: tuple[dict[str, object], ...]
    severity_chart: ChartSeries
    trend_chart: ChartSeries


def build_dashboard() -> DashboardSnapshot:
    overview = build_overview()
    critical = next(
        (
            item.count
            for item in overview.incidents.by_severity
            if item.key == Incident.Severity.CRITICAL
        ),
        0,
    )
    markers = tuple(
        {
            "id": str(station.pk),
            "name": station.name,
            "code": station.code,
            "city": station.city,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "url": reverse("station_detail", args=[station.pk]),
        }
        for station in station_directory(is_active=True)[:MAX_MAP_STATIONS]
    )
    return DashboardSnapshot(
        overview=overview,
        critical_incidents=critical,
        recent_incidents=tuple(incident_directory()[:RECENT_LIMIT]),
        recent_services=tuple(
            TrainService.objects.select_related("origin", "destination").order_by("-imported_at")[
                :RECENT_LIMIT
            ]
        ),
        station_markers=markers,
        severity_chart=ChartSeries(
            labels=tuple(item.label for item in overview.incidents.by_severity),
            values=tuple(item.count for item in overview.incidents.by_severity),
        ),
        trend_chart=ChartSeries(
            labels=tuple(item.label for item in overview.incidents.volume_by_month),
            values=tuple(item.count for item in overview.incidents.volume_by_month),
        ),
    )
