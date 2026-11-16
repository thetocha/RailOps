"""Operations map snapshot. Views render this; JavaScript only draws markers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.urls import reverse

from apps.incidents.models import Incident
from apps.incidents.spatial import (
    MAX_MAP_INCIDENTS,
    active_incidents_for_map,
    incidents_within_radius,
)
from apps.infrastructure.models import Station
from apps.infrastructure.spatial import (
    MAX_NEARBY_RESULTS,
    origin_from_lon_lat,
    stations_within_radius,
)

MAX_MAP_STATIONS = 200


@dataclass(frozen=True)
class OperationsMap:
    origin: dict[str, object] | None
    stations: tuple[dict[str, object], ...]
    incidents: tuple[dict[str, object], ...]


def _station_item(station: Station, *, distance_label: str = "") -> dict[str, object]:
    return {
        "kind": "station",
        "name": station.name,
        "code": station.code,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "url": reverse("station_detail", args=[station.pk]),
        "distance_label": distance_label,
    }


def _incident_item(incident: Incident) -> dict[str, object]:
    return {
        "kind": "incident",
        "title": incident.title,
        "severity": incident.severity,
        "severity_label": incident.get_severity_display(),
        "status": incident.status,
        "latitude": incident.station.latitude,
        "longitude": incident.station.longitude,
        "station_name": incident.station.name,
        "url": reverse("incident_detail", args=[incident.pk]),
    }


def build_operations_map(
    *,
    longitude: Decimal | float | None = None,
    latitude: Decimal | float | None = None,
    radius_meters: int | None = None,
    include_incidents: bool = True,
) -> OperationsMap:
    if longitude is not None and latitude is not None and radius_meters is not None:
        origin = origin_from_lon_lat(longitude=longitude, latitude=latitude)
        nearby = stations_within_radius(
            origin=origin,
            radius_meters=radius_meters,
            limit=MAX_NEARBY_RESULTS,
        )
        incidents: tuple[dict[str, object], ...] = ()
        if include_incidents:
            incidents = tuple(
                _incident_item(incident)
                for incident in incidents_within_radius(
                    origin=origin,
                    radius_meters=radius_meters,
                    limit=MAX_MAP_INCIDENTS,
                )
            )
        return OperationsMap(
            origin={
                "latitude": float(latitude),
                "longitude": float(longitude),
                "radius_meters": radius_meters,
            },
            stations=tuple(
                _station_item(item.station, distance_label=item.distance_label) for item in nearby
            ),
            incidents=incidents,
        )
    stations = tuple(
        _station_item(station)
        for station in Station.objects.filter(is_active=True).order_by("name")[:MAX_MAP_STATIONS]
    )
    incidents = ()
    if include_incidents:
        incidents = tuple(_incident_item(incident) for incident in active_incidents_for_map())
    return OperationsMap(origin=None, stations=stations, incidents=incidents)
