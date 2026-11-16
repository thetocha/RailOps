from __future__ import annotations

import pytest
from django.contrib.auth.models import Permission
from django.contrib.gis.geos import Point
from django.test import Client

from apps.accounts.models import User
from apps.infrastructure.models import Station
from apps.infrastructure.tests.conftest import TEST_PASSWORD, redirect_location

pytestmark = pytest.mark.django_db


@pytest.fixture
def potsdam(db: None) -> Station:
    return Station.objects.create(
        name="Potsdam Hauptbahnhof",
        code="PD",
        city="Potsdam",
        location=Point(13.0655, 52.3912, srid=4326),
    )


def test_user_without_station_permission_cannot_search_nearby(client: Client, db: None) -> None:
    user = User.objects.create_user(
        username="no_stations_nearby",
        email="no_stations_nearby@example.com",
        password=TEST_PASSWORD,
    )
    user.user_permissions.add(
        Permission.objects.get(codename="access_dashboard", content_type__app_label="accounts")
    )
    client.force_login(user)
    assert client.get("/stations/nearby/").status_code == 403


def test_unauthenticated_nearby_redirects(client: Client) -> None:
    response = client.get("/stations/nearby/")
    assert response.status_code == 302
    assert "/accounts/login/" in redirect_location(response)


def test_unrelated_query_does_not_bind_form(client: Client, viewer: User) -> None:
    client.force_login(viewer)
    response = client.get("/stations/nearby/", {"utm_source": "newsletter"})
    assert response.status_code == 200
    assert response.context["form"].is_bound is False
    assert response.context["results"] == []


def test_nearby_search_lists_potsdam(
    client: Client, viewer: User, berlin: Station, hamburg: Station, potsdam: Station
) -> None:
    client.force_login(viewer)
    response = client.get(
        "/stations/nearby/",
        {"latitude": "52.5255", "longitude": "13.3695", "radius_meters": "50000"},
    )
    assert response.status_code == 200
    assert b"Potsdam Hauptbahnhof" in response.content
    assert b"Hamburg Hauptbahnhof" not in response.content
    assert b"ST_DWithin" not in response.content
    payload = response.context["map_payload"]
    codes = {item["code"] for item in payload["stations"]}
    assert codes == {"BHF", "PD"}


def test_invalid_radius_does_not_query(client: Client, viewer: User, berlin: Station) -> None:
    client.force_login(viewer)
    response = client.get(
        "/stations/nearby/",
        {"latitude": "52.5255", "longitude": "13.3695", "radius_meters": "900000"},
    )
    assert response.status_code == 200
    assert response.context["results"] == []
    assert (
        b"Radius must be between" in response.content
        or b"Ensure this value is less than or equal" in response.content
    )


def test_station_detail_shows_nearest(
    client: Client, viewer: User, berlin: Station, potsdam: Station
) -> None:
    client.force_login(viewer)
    response = client.get(f"/stations/{berlin.pk}/")
    assert response.status_code == 200
    assert b"Potsdam Hauptbahnhof" in response.content
    assert b"Nearest other station" in response.content
