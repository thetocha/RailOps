from __future__ import annotations

import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.infrastructure.geo import point_from_lon_lat
from apps.infrastructure.models import RailwayLine, Station
from apps.infrastructure.services import (
    create_railway_line,
    create_station,
    deactivate_railway_line,
    deactivate_station,
    update_railway_line,
    update_station,
)

pytestmark = pytest.mark.django_db


def test_create_station_normalizes_code_and_persists_point(administrator: User) -> None:
    station = create_station(
        actor=administrator,
        name="  Leipzig Hbf ",
        code="l-hbf",
        city=" Leipzig ",
        location=point_from_lon_lat(12.381, 51.345),
    )
    assert station.code == "L-HBF"
    assert station.name == "Leipzig Hbf"
    assert station.city == "Leipzig"
    assert station.location.srid == 4326


def test_create_station_rejects_duplicate_code(administrator: User, berlin: Station) -> None:
    with pytest.raises(ValidationError) as exc:
        create_station(
            actor=administrator,
            name="Copy",
            code="bhf",
            city="Berlin",
            location=Point(13.37, 52.52, srid=4326),
        )
    assert "code" in exc.value.message_dict


def test_viewer_cannot_create_or_deactivate_station(viewer: User, berlin: Station) -> None:
    with pytest.raises(PermissionDenied):
        create_station(
            actor=viewer,
            name="Forbidden",
            code="FORB",
            city="Berlin",
            location=Point(13.37, 52.52, srid=4326),
        )
    with pytest.raises(PermissionDenied):
        deactivate_station(actor=viewer, station=berlin)
    berlin.refresh_from_db()
    assert berlin.is_active is True


def test_dispatcher_cannot_update_station(dispatcher: User, berlin: Station) -> None:
    with pytest.raises(PermissionDenied):
        update_station(
            actor=dispatcher,
            station=berlin,
            name=berlin.name,
            code=berlin.code,
            city="Hacked",
            location=berlin.location,
            is_active=True,
        )
    berlin.refresh_from_db()
    assert berlin.city == "Berlin"


def test_deactivate_station_is_idempotent(administrator: User, berlin: Station) -> None:
    deactivate_station(actor=administrator, station=berlin)
    berlin.refresh_from_db()
    assert berlin.is_active is False
    deactivate_station(actor=administrator, station=berlin)
    berlin.refresh_from_db()
    assert berlin.is_active is False


def test_create_line_requires_active_stations(
    administrator: User,
    berlin: Station,
    hamburg: Station,
) -> None:
    hamburg.is_active = False
    hamburg.save(update_fields=["is_active"])
    with pytest.raises(ValidationError) as exc:
        create_railway_line(
            actor=administrator,
            name="Broken",
            code="BRK",
            start_station=berlin,
            end_station=hamburg,
        )
    assert "end_station" in exc.value.message_dict


def test_update_line_allows_existing_inactive_endpoint(
    administrator: User,
    berlin_hamburg: RailwayLine,
    berlin: Station,
    hamburg: Station,
) -> None:
    hamburg.is_active = False
    hamburg.save(update_fields=["is_active"])
    updated = update_railway_line(
        actor=administrator,
        line=berlin_hamburg,
        name="Berlin–Hamburg Express",
        code="BE-HH",
        start_station=berlin,
        end_station=hamburg,
        is_active=True,
    )
    assert updated.name == "Berlin–Hamburg Express"


def test_deactivate_line(administrator: User, berlin_hamburg: RailwayLine) -> None:
    deactivate_railway_line(actor=administrator, line=berlin_hamburg)
    berlin_hamburg.refresh_from_db()
    assert berlin_hamburg.is_active is False


def test_point_from_lon_lat_rejects_out_of_range() -> None:
    with pytest.raises(ValidationError):
        point_from_lon_lat(200, 10)
    with pytest.raises(ValidationError):
        point_from_lon_lat(10, 100)
