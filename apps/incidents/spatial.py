"""PostGIS incident queries keyed by station location."""

from __future__ import annotations

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import QuerySet

from apps.incidents.models import Incident
from apps.infrastructure.spatial import require_wgs84, validate_radius_meters

ACTIVE_MAP_STATUSES = (Incident.Status.OPEN, Incident.Status.IN_PROGRESS)
MAX_MAP_INCIDENTS = 200


def incidents_within_radius(
    *,
    origin: Point,
    radius_meters: int,
    limit: int = MAX_MAP_INCIDENTS,
) -> QuerySet[Incident]:
    origin = require_wgs84(origin)
    radius_meters = validate_radius_meters(radius_meters)
    return (
        Incident.objects.filter(
            status__in=ACTIVE_MAP_STATUSES,
            station__is_active=True,
            station__location__dwithin=(origin, D(m=radius_meters)),
        )
        .select_related("station")
        .annotate(distance=Distance("station__location", origin))
        .order_by("distance", "-reported_at")[:limit]
    )


def active_incidents_for_map(*, limit: int = MAX_MAP_INCIDENTS) -> QuerySet[Incident]:
    return (
        Incident.objects.filter(status__in=ACTIVE_MAP_STATUSES, station__is_active=True)
        .select_related("station")
        .order_by("-reported_at", "title")[:limit]
    )
