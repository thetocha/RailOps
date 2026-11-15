"""Coordinate helpers. Point uses (longitude, latitude) with SRID 4326."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError

MIN_LATITUDE = Decimal("-90")
MAX_LATITUDE = Decimal("90")
MIN_LONGITUDE = Decimal("-180")
MAX_LONGITUDE = Decimal("180")


def point_from_lon_lat(longitude: Decimal | float, latitude: Decimal | float) -> Point:
    lon = Decimal(str(longitude))
    lat = Decimal(str(latitude))
    if lon < MIN_LONGITUDE or lon > MAX_LONGITUDE:
        raise ValidationError("Longitude must be between -180 and 180.")
    if lat < MIN_LATITUDE or lat > MAX_LATITUDE:
        raise ValidationError("Latitude must be between -90 and 90.")
    return Point(float(lon), float(lat), srid=4326)
