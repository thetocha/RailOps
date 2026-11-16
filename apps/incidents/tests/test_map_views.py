from __future__ import annotations

import pytest
from django.contrib.auth.models import Permission
from django.contrib.gis.geos import Point
from django.test import Client

from apps.accounts.models import User
from apps.incidents.models import Incident
from apps.incidents.services import create_incident
from apps.incidents.tests.conftest import TEST_PASSWORD, redirect_location
from apps.infrastructure.models import Station

pytestmark = pytest.mark.django_db


@pytest.fixture
def potsdam(db: None) -> Station:
    return Station.objects.create(
        name="Potsdam Hauptbahnhof",
        code="PD",
        city="Potsdam",
        location=Point(13.0655, 52.3912, srid=4326),
    )


def test_user_without_station_permission_is_forbidden(client: Client, db: None) -> None:
    user = User.objects.create_user(
        username="no_stations",
        email="no_stations@example.com",
        password=TEST_PASSWORD,
    )
    user.user_permissions.add(
        Permission.objects.get(codename="access_dashboard", content_type__app_label="accounts")
    )
    client.force_login(user)
    assert client.get("/map/").status_code == 403


def test_station_view_without_incident_view_hides_incidents(
    client: Client,
    dispatcher: User,
    berlin: Station,
    db: None,
) -> None:
    create_incident(
        actor=dispatcher,
        title="Hidden from station-only user",
        description="Needs incident permission.",
        station=berlin,
        category=Incident.Category.OTHER,
        severity=Incident.Severity.LOW,
    )
    user = User.objects.create_user(
        username="stations_only",
        email="stations_only@example.com",
        password=TEST_PASSWORD,
    )
    user.user_permissions.add(
        Permission.objects.get(codename="access_dashboard", content_type__app_label="accounts"),
        Permission.objects.get(codename="view_station", content_type__app_label="infrastructure"),
    )
    client.force_login(user)
    response = client.get("/map/")
    assert response.status_code == 200
    assert response.context["map_payload"]["incidents"] == []
    assert response.context["map_payload"]["stations"][0]["code"] == "BHF"


def test_unauthenticated_map_redirects(client: Client) -> None:
    response = client.get("/map/")
    assert response.status_code == 302
    assert "/accounts/login/" in redirect_location(response)


def test_viewer_sees_stations_and_incident_markers(
    client: Client,
    viewer: User,
    dispatcher: User,
    berlin: Station,
    hamburg: Station,
) -> None:
    create_incident(
        actor=dispatcher,
        title="Ice on the platform",
        description="Critical obstruction.",
        station=berlin,
        category=Incident.Category.WEATHER,
        severity=Incident.Severity.CRITICAL,
    )
    client.force_login(viewer)
    response = client.get("/map/")
    assert response.status_code == 200
    assert b"Berlin Hauptbahnhof" in response.content
    payload = response.context["map_payload"]
    assert {item["code"] for item in payload["stations"]} == {"BHF", "HH"}
    assert payload["incidents"][0]["title"] == "Ice on the platform"
    assert payload["incidents"][0]["severity"] == Incident.Severity.CRITICAL


def test_spatial_filter_hides_hamburg_incident(
    client: Client,
    viewer: User,
    dispatcher: User,
    berlin: Station,
    hamburg: Station,
    potsdam: Station,
) -> None:
    create_incident(
        actor=dispatcher,
        title="Berlin only",
        description="In radius.",
        station=berlin,
        category=Incident.Category.OTHER,
        severity=Incident.Severity.MEDIUM,
    )
    create_incident(
        actor=dispatcher,
        title="Hamburg only",
        description="Out of radius.",
        station=hamburg,
        category=Incident.Category.OTHER,
        severity=Incident.Severity.LOW,
    )
    client.force_login(viewer)
    response = client.get(
        "/map/",
        {"latitude": "52.5255", "longitude": "13.3695", "radius_meters": "50000"},
    )
    assert response.status_code == 200
    titles = {item["title"] for item in response.context["map_payload"]["incidents"]}
    assert titles == {"Berlin only"}
    codes = {item["code"] for item in response.context["map_payload"]["stations"]}
    assert "HH" not in codes
    assert "BHF" in codes
