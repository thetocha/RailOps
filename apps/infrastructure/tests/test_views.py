from __future__ import annotations

import pytest
from django.contrib.gis.geos import Point
from django.test import Client

from apps.accounts.models import User
from apps.infrastructure.models import RailwayLine, Station
from apps.infrastructure.tests.conftest import redirect_location

pytestmark = pytest.mark.django_db


def _station_post(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Cologne Hbf",
        "code": "KN",
        "city": "Cologne",
        "latitude": "50.943",
        "longitude": "6.958",
        "is_active": "on",
    }
    payload.update(overrides)
    return payload


def test_anonymous_users_are_redirected_from_station_pages(client: Client, berlin: Station) -> None:
    list_response = client.get("/stations/")
    assert list_response.status_code == 302
    assert "/accounts/login/" in redirect_location(list_response)
    detail_response = client.get(f"/stations/{berlin.pk}/")
    assert detail_response.status_code == 302


def test_viewer_can_list_and_view_but_cannot_mutate(
    client: Client,
    viewer: User,
    berlin: Station,
    berlin_hamburg: RailwayLine,
) -> None:
    client.force_login(viewer)
    listing = client.get("/stations/")
    assert listing.status_code == 200
    assert b"Berlin Hauptbahnhof" in listing.content
    assert b"Create station" not in listing.content
    detail = client.get(f"/stations/{berlin.pk}/")
    assert detail.status_code == 200
    assert client.get("/stations/create/").status_code == 403
    create_response = client.post("/stations/create/", _station_post())
    assert create_response.status_code == 403
    assert not Station.objects.filter(code="KN").exists()
    assert (
        client.post(f"/stations/{berlin.pk}/edit/", _station_post(name="Hacked")).status_code == 403
    )
    berlin.refresh_from_db()
    assert berlin.name == "Berlin Hauptbahnhof"
    assert client.post(f"/stations/{berlin.pk}/deactivate/").status_code == 403
    berlin.refresh_from_db()
    assert berlin.is_active is True
    assert client.get("/lines/").status_code == 200
    assert client.get("/lines/create/").status_code == 403
    assert client.post(f"/lines/{berlin_hamburg.pk}/deactivate/").status_code == 403


def test_dispatcher_can_view_infrastructure_but_cannot_create(
    client: Client,
    dispatcher: User,
    berlin: Station,
) -> None:
    client.force_login(dispatcher)
    assert client.get("/stations/").status_code == 200
    assert client.get(f"/stations/{berlin.pk}/").status_code == 200
    assert client.get("/lines/").status_code == 200
    assert client.post("/stations/create/", _station_post()).status_code == 403
    assert not Station.objects.filter(code="KN").exists()


def test_administrator_can_create_update_and_deactivate_station(
    client: Client,
    administrator: User,
    berlin: Station,
) -> None:
    client.force_login(administrator)
    create_page = client.get("/stations/create/")
    assert create_page.status_code == 200
    created = client.post("/stations/create/", _station_post(), follow=False)
    assert created.status_code == 302
    station = Station.objects.get(code="KN")
    assert station.city == "Cologne"
    assert station.latitude == pytest.approx(50.943)
    edit = client.post(
        f"/stations/{station.pk}/edit/",
        _station_post(name="Köln Hbf", city="Köln"),
    )
    assert edit.status_code == 302
    station.refresh_from_db()
    assert station.name == "Köln Hbf"
    deactivate = client.post(f"/stations/{station.pk}/deactivate/")
    assert deactivate.status_code == 302
    station.refresh_from_db()
    assert station.is_active is False


def test_station_list_search_filter_and_pagination(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    for index in range(21):
        Station.objects.create(
            name=f"Station {index:02d}",
            code=f"S{index:02d}",
            city="Berlin" if index % 2 == 0 else "Hamburg",
            location=Point(13.4, 52.5, srid=4326),
        )
    page_one = client.get("/stations/?status=all")
    assert page_one.status_code == 200
    assert b"Page 1 of" in page_one.content
    page_two = client.get("/stations/?status=all&page=2")
    assert page_two.status_code == 200
    search = client.get("/stations/?q=S20&status=all")
    assert search.status_code == 200
    assert b"S20" in search.content
    assert b"S01" not in search.content
    inactive = Station.objects.get(code="S00")
    inactive.is_active = False
    inactive.save(update_fields=["is_active"])
    active_only = client.get("/stations/?status=active")
    assert b"S00" not in active_only.content
    inactive_only = client.get("/stations/?status=inactive")
    assert b"S00" in inactive_only.content


def test_administrator_can_manage_railway_lines(
    client: Client,
    administrator: User,
    berlin: Station,
    hamburg: Station,
    berlin_hamburg: RailwayLine,
) -> None:
    client.force_login(administrator)
    created = client.post(
        "/lines/create/",
        {
            "name": "Second line",
            "code": "sec",
            "start_station": str(hamburg.pk),
            "end_station": str(berlin.pk),
            "is_active": "on",
        },
    )
    assert created.status_code == 302
    line = RailwayLine.objects.get(code="SEC")
    assert line.start_station_id == hamburg.pk
    updated = client.post(
        f"/lines/{line.pk}/edit/",
        {
            "name": "Hamburg–Berlin",
            "code": "SEC",
            "start_station": str(hamburg.pk),
            "end_station": str(berlin.pk),
            "is_active": "on",
        },
    )
    assert updated.status_code == 302
    line.refresh_from_db()
    assert line.name == "Hamburg–Berlin"
    deactivated = client.post(f"/lines/{berlin_hamburg.pk}/deactivate/")
    assert deactivated.status_code == 302
    berlin_hamburg.refresh_from_db()
    assert berlin_hamburg.is_active is False


def test_invalid_station_form_redisplays_errors(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    response = client.post(
        "/stations/create/",
        {
            "name": "",
            "code": "??",
            "city": "",
            "latitude": "200",
            "longitude": "10",
        },
    )
    assert response.status_code == 200
    assert b"required" in response.content.lower() or b"Code must start" in response.content
    assert not Station.objects.filter(code="??").exists()


def test_line_list_search_finds_station_code(
    client: Client,
    administrator: User,
    berlin_hamburg: RailwayLine,
) -> None:
    client.force_login(administrator)
    response = client.get("/lines/?q=BHF&status=all")
    assert response.status_code == 200
    assert b"Berlin" in response.content
