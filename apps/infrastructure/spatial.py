"""PostGIS station queries. Do not approximate distances in Python."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.exceptions import ValidationError

from apps.infrastructure.geo import point_from_lon_lat
from apps.infrastructure.models import Station

MIN_RADIUS_METERS = 1
MAX_RADIUS_METERS = 500_000
DEFAULT_RADIUS_METERS = 50_000
MAX_NEARBY_RESULTS = 50


@dataclass(frozen=True)
class StationDistance:
    station: Station
    distance_meters: float

    @property
    def distance_label(self) -> str:
        return format_distance_meters(self.distance_meters)


def validate_radius_meters(radius_meters: int) -> int:
    if radius_meters < MIN_RADIUS_METERS or radius_meters > MAX_RADIUS_METERS:
        raise ValidationError(
            {
                "radius_meters": (
                    f"Radius must be between {MIN_RADIUS_METERS} and {MAX_RADIUS_METERS} metres."
                )
            }
        )
    return radius_meters


def origin_from_lon_lat(*, longitude: Decimal | float, latitude: Decimal | float) -> Point:
    return point_from_lon_lat(longitude, latitude)


def require_wgs84(origin: Point) -> Point:
    if origin.srid != 4326:
        raise ValidationError("Origin must use SRID 4326.")
    return origin


def _distance_meters(value: object) -> float:
    meters = getattr(value, "m", None)
    if meters is not None:
        return float(meters)
    return float(value)  # type: ignore[arg-type]


def stations_within_radius(
    *,
    origin: Point,
    radius_meters: int,
    is_active: bool | None = True,
    limit: int = MAX_NEARBY_RESULTS,
) -> list[StationDistance]:
    origin = require_wgs84(origin)
    radius_meters = validate_radius_meters(radius_meters)
    queryset = Station.objects.filter(location__dwithin=(origin, D(m=radius_meters)))
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    rows = queryset.annotate(distance=Distance("location", origin)).order_by("distance", "name")[
        :limit
    ]
    return [
        StationDistance(
            station=row,
            distance_meters=_distance_meters(row.distance),
        )
        for row in rows
    ]


def nearest_station(
    *,
    origin: Point,
    is_active: bool | None = True,
    exclude_id: UUID | None = None,
) -> StationDistance | None:
    origin = require_wgs84(origin)
    queryset = Station.objects.all()
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    if exclude_id is not None:
        queryset = queryset.exclude(pk=exclude_id)
    row = (
        queryset.annotate(distance=Distance("location", origin))
        .order_by("distance", "name")
        .first()
    )
    if row is None:
        return None
    return StationDistance(
        station=row,
        distance_meters=_distance_meters(row.distance),
    )


def format_distance_meters(meters: float) -> str:
    if meters >= 1000:
        return f"{meters / 1000:.1f} km"
    return f"{int(round(meters))} m"
