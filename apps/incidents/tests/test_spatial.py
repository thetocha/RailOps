from __future__ import annotations

import pytest
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from apps.accounts.models import User
from apps.incidents.models import Incident
from apps.incidents.services import create_incident
from apps.incidents.spatial import incidents_within_radius
from apps.infrastructure.models import Station
from apps.infrastructure.spatial import origin_from_lon_lat

pytestmark = pytest.mark.django_db


@pytest.fixture
def potsdam(db: None) -> Station:
    return Station.objects.create(
        name="Potsdam Hauptbahnhof",
        code="PD",
        city="Potsdam",
        location=Point(13.0655, 52.3912, srid=4326),
    )


def test_incident_radius_sql_uses_dwithin(berlin: Station) -> None:
    origin = origin_from_lon_lat(longitude=berlin.longitude, latitude=berlin.latitude)
    sql = str(Incident.objects.filter(station__location__dwithin=(origin, D(m=50_000))).query)
    assert "ST_DWithin" in sql


def test_incidents_within_radius_excludes_distant_station(
    dispatcher: User,
    berlin: Station,
    hamburg: Station,
    potsdam: Station,
) -> None:
    local = create_incident(
        actor=dispatcher,
        title="Signal at Berlin",
        description="Local failure.",
        station=berlin,
        category=Incident.Category.SIGNAL_FAILURE,
        severity=Incident.Severity.HIGH,
    )
    create_incident(
        actor=dispatcher,
        title="Delay in Hamburg",
        description="Far away.",
        station=hamburg,
        category=Incident.Category.OPERATIONAL_DELAY,
        severity=Incident.Severity.LOW,
    )
    origin = origin_from_lon_lat(longitude=potsdam.longitude, latitude=potsdam.latitude)
    matches = list(incidents_within_radius(origin=origin, radius_meters=50_000))
    assert [incident.pk for incident in matches] == [local.pk]


def test_closed_incidents_are_not_mapped(dispatcher: User, berlin: Station) -> None:
    incident = create_incident(
        actor=dispatcher,
        title="Already done",
        description="Closed later.",
        station=berlin,
        category=Incident.Category.OTHER,
        severity=Incident.Severity.LOW,
    )
    Incident.objects.filter(pk=incident.pk).update(status=Incident.Status.CLOSED)
    origin = origin_from_lon_lat(longitude=berlin.longitude, latitude=berlin.latitude)
    assert list(incidents_within_radius(origin=origin, radius_meters=50_000)) == []
