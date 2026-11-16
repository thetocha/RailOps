from __future__ import annotations

import pytest
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.exceptions import ValidationError

from apps.infrastructure.models import Station
from apps.infrastructure.spatial import (
    MAX_RADIUS_METERS,
    format_distance_meters,
    nearest_station,
    origin_from_lon_lat,
    stations_within_radius,
    validate_radius_meters,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def potsdam(db: None) -> Station:
    return Station.objects.create(
        name="Potsdam Hauptbahnhof",
        code="PD",
        city="Potsdam",
        location=Point(13.0655, 52.3912, srid=4326),
    )


def test_dwithin_sql_uses_postgis(berlin: Station) -> None:
    origin = origin_from_lon_lat(longitude=berlin.longitude, latitude=berlin.latitude)
    sql = str(Station.objects.filter(location__dwithin=(origin, D(m=50_000))).query)
    assert "ST_DWithin" in sql


def test_nearest_sql_uses_st_distance(berlin: Station) -> None:
    origin = origin_from_lon_lat(longitude=berlin.longitude, latitude=berlin.latitude)
    sql = str(Station.objects.annotate(distance=Distance("location", origin)).query)
    assert "ST_Distance" in sql


def test_nearby_includes_potsdam_not_hamburg(
    berlin: Station, hamburg: Station, potsdam: Station
) -> None:
    origin = origin_from_lon_lat(longitude=berlin.longitude, latitude=berlin.latitude)
    matches = stations_within_radius(origin=origin, radius_meters=50_000)
    codes = {item.station.code for item in matches}
    assert codes == {"BHF", "PD"}
    potsdam_match = next(item for item in matches if item.station.code == "PD")
    assert 20_000 < potsdam_match.distance_meters < 40_000


def test_inactive_station_excluded_by_default(berlin: Station, potsdam: Station) -> None:
    potsdam.is_active = False
    potsdam.save(update_fields=["is_active"])
    origin = origin_from_lon_lat(longitude=berlin.longitude, latitude=berlin.latitude)
    codes = {
        item.station.code for item in stations_within_radius(origin=origin, radius_meters=50_000)
    }
    assert codes == {"BHF"}


def test_nearest_other_station_is_potsdam(
    berlin: Station, hamburg: Station, potsdam: Station
) -> None:
    result = nearest_station(origin=berlin.location, exclude_id=berlin.pk)
    assert result is not None
    assert result.station.code == "PD"


def test_nearest_empty() -> None:
    origin = origin_from_lon_lat(longitude=13.0, latitude=52.5)
    assert nearest_station(origin=origin) is None


def test_radius_bounds() -> None:
    with pytest.raises(ValidationError):
        validate_radius_meters(0)
    with pytest.raises(ValidationError):
        validate_radius_meters(MAX_RADIUS_METERS + 1)
    assert validate_radius_meters(50_000) == 50_000


def test_origin_rejects_wrong_srid(berlin: Station) -> None:
    bad = Point(13.3695, 52.5255, srid=3857)
    with pytest.raises(ValidationError):
        stations_within_radius(origin=bad, radius_meters=1000)


def test_format_distance() -> None:
    assert format_distance_meters(250) == "250 m"
    assert format_distance_meters(27500) == "27.5 km"
