from __future__ import annotations

import pytest
from django.contrib.gis.geos import LineString, Point
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from apps.infrastructure.models import RailwayLine, Station

pytestmark = pytest.mark.django_db


def test_station_requires_unique_code(berlin: Station) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Station.objects.create(
            name="Other Berlin",
            code="BHF",
            city="Berlin",
            location=Point(13.37, 52.52, srid=4326),
        )


def test_station_empty_code_rejected() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Station.objects.create(
            name="Nameless Code",
            code="",
            city="Berlin",
            location=Point(13.37, 52.52, srid=4326),
        )


def test_station_str_and_coordinates(berlin: Station) -> None:
    assert str(berlin) == "Berlin Hauptbahnhof (BHF)"
    assert berlin.latitude == pytest.approx(52.5255)
    assert berlin.longitude == pytest.approx(13.3695)
    assert berlin.is_active is True
    assert berlin.created_at <= timezone.now()
    assert berlin.updated_at <= timezone.now()


def test_station_location_is_geography_4326_with_spatial_index() -> None:
    field = Station._meta.get_field("location")
    assert field.srid == 4326
    assert field.geography is True
    assert field.spatial_index is True


def test_station_location_gist_index_exists() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT indexdef
            FROM pg_indexes
            WHERE tablename = 'infrastructure_station'
              AND indexdef ILIKE '%gist%'
            """
        )
        rows = cursor.fetchall()
    assert rows


def test_railway_line_unique_code(
    berlin_hamburg: RailwayLine, berlin: Station, hamburg: Station
) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        RailwayLine.objects.create(
            name="Duplicate",
            code="BE-HH",
            start_station=berlin,
            end_station=hamburg,
        )


def test_railway_line_protects_station_delete(berlin_hamburg: RailwayLine, berlin: Station) -> None:
    with pytest.raises(ProtectedError), transaction.atomic():
        berlin.delete()
    assert Station.objects.filter(pk=berlin.pk).exists()
    assert RailwayLine.objects.filter(pk=berlin_hamburg.pk).exists()


def test_railway_line_geometry_is_optional_and_not_inferred(
    berlin: Station,
    hamburg: Station,
) -> None:
    line = RailwayLine.objects.create(
        name="No geometry",
        code="NOGEO",
        start_station=berlin,
        end_station=hamburg,
    )
    assert line.geometry is None
    stored = LineString((13.3695, 52.5255), (10.0069, 53.5528), srid=4326)
    line.geometry = stored
    line.save()
    line.refresh_from_db()
    assert line.geometry is not None
    assert line.geometry.srid == 4326


def test_railway_line_str(berlin_hamburg: RailwayLine) -> None:
    assert str(berlin_hamburg) == "Berlin–Hamburg (BE-HH)"
