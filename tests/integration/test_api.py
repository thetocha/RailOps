from __future__ import annotations

import pytest
from django.test import Client
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.incidents.models import Incident
from apps.infrastructure.models import Station
from apps.integrations.providers.mock import MockRailwayProvider
from apps.integrations.services import synchronize_timetables
from apps.timetables.models import TrainService

pytestmark = pytest.mark.django_db


def test_unauthenticated_api_returns_401_not_login_redirect(api_client: APIClient) -> None:
    response = api_client.get("/api/v1/stations/")
    assert response.status_code == 401
    assert "login" not in str(response.headers.get("Location", "")).lower()
    assert "detail" in response.json()


def test_viewer_can_list_stations_but_cannot_create(
    api_client: APIClient,
    viewer: User,
    berlin: Station,
) -> None:
    api_client.force_login(viewer)
    listing = api_client.get("/api/v1/stations/")
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    assert listing.json()["results"][0]["code"] == "BHF"
    assert listing.json()["results"][0]["latitude"] == pytest.approx(52.5255)
    created = api_client.post(
        "/api/v1/stations/",
        {
            "name": "Leipzig",
            "code": "L",
            "city": "Leipzig",
            "latitude": 51.3455,
            "longitude": 12.381,
        },
        format="json",
    )
    assert created.status_code == 403


def test_administrator_can_create_and_patch_station(
    api_client: APIClient,
    administrator: User,
) -> None:
    api_client.force_login(administrator)
    created = api_client.post(
        "/api/v1/stations/",
        {
            "name": "Leipzig Hauptbahnhof",
            "code": "l",
            "city": "Leipzig",
            "latitude": 51.3455,
            "longitude": 12.381,
            "is_active": True,
        },
        format="json",
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["code"] == "L"
    station_id = payload["id"]
    patched = api_client.patch(
        f"/api/v1/stations/{station_id}/",
        {"city": "Leipzig Mitte"},
        format="json",
    )
    assert patched.status_code == 200
    assert patched.json()["city"] == "Leipzig Mitte"


def test_invalid_coordinates_are_rejected(
    api_client: APIClient,
    administrator: User,
) -> None:
    api_client.force_login(administrator)
    response = api_client.post(
        "/api/v1/stations/",
        {
            "name": "Nowhere",
            "code": "XX",
            "city": "Nowhere",
            "latitude": 100,
            "longitude": 12,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "latitude" in response.json()


def test_dispatcher_can_create_incident_but_not_station(
    api_client: APIClient,
    dispatcher: User,
    berlin: Station,
) -> None:
    api_client.force_login(dispatcher)
    station_create = api_client.post(
        "/api/v1/stations/",
        {
            "name": "Leipzig",
            "code": "L",
            "city": "Leipzig",
            "latitude": 51.3,
            "longitude": 12.3,
        },
        format="json",
    )
    assert station_create.status_code == 403
    created = api_client.post(
        "/api/v1/incidents/",
        {
            "title": "Signal failure",
            "description": "Home signal stuck at red.",
            "station": str(berlin.pk),
            "category": "signal_failure",
            "severity": "high",
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["status"] == "open"
    assert created.json()["station_code"] == "BHF"


def test_viewer_cannot_create_or_transition_incident(
    api_client: APIClient,
    viewer: User,
    dispatcher: User,
    berlin: Station,
) -> None:
    api_client.force_login(dispatcher)
    created = api_client.post(
        "/api/v1/incidents/",
        {
            "title": "Obstruction",
            "description": "Tree on the track.",
            "station": str(berlin.pk),
            "category": "track_obstruction",
            "severity": "medium",
        },
        format="json",
    )
    incident_id = created.json()["id"]
    api_client.force_login(viewer)
    listing = api_client.get("/api/v1/incidents/")
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    forbidden = api_client.post(
        f"/api/v1/incidents/{incident_id}/transition/",
        {"status": "in_progress"},
        format="json",
    )
    assert forbidden.status_code == 403


def test_dispatcher_can_transition_incident(
    api_client: APIClient,
    dispatcher: User,
    berlin: Station,
) -> None:
    api_client.force_login(dispatcher)
    created = api_client.post(
        "/api/v1/incidents/",
        {
            "title": "Weather delay",
            "description": "Ice on overhead line.",
            "station": str(berlin.pk),
            "category": "weather",
            "severity": "high",
        },
        format="json",
    )
    incident_id = created.json()["id"]
    transitioned = api_client.post(
        f"/api/v1/incidents/{incident_id}/transition/",
        {"status": "in_progress", "comment": "Crew dispatched."},
        format="json",
    )
    assert transitioned.status_code == 200
    assert transitioned.json()["status"] == "in_progress"
    assert any(event["event_type"] == "status_changed" for event in transitioned.json()["events"])
    invalid = api_client.post(
        f"/api/v1/incidents/{incident_id}/transition/",
        {"status": "closed"},
        format="json",
    )
    assert invalid.status_code == 400
    assert "detail" in invalid.json()
    assert Incident.objects.get(pk=incident_id).status == Incident.Status.IN_PROGRESS


def test_incident_list_filters_by_status(
    api_client: APIClient,
    dispatcher: User,
    berlin: Station,
) -> None:
    api_client.force_login(dispatcher)
    api_client.post(
        "/api/v1/incidents/",
        {
            "title": "Open one",
            "description": "Still open.",
            "station": str(berlin.pk),
            "category": "other",
            "severity": "low",
        },
        format="json",
    )
    listing = api_client.get("/api/v1/incidents/", {"status": "open"})
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    empty = api_client.get("/api/v1/incidents/", {"status": "closed"})
    assert empty.json()["count"] == 0


def test_station_list_is_paginated(
    api_client: APIClient,
    administrator: User,
) -> None:
    api_client.force_login(administrator)
    for index in range(21):
        api_client.post(
            "/api/v1/stations/",
            {
                "name": f"Station {index}",
                "code": f"S{index}",
                "city": "Berlin",
                "latitude": 52.5,
                "longitude": 13.4,
            },
            format="json",
        )
    page = api_client.get("/api/v1/stations/")
    assert page.status_code == 200
    body = page.json()
    assert body["count"] == 21
    assert len(body["results"]) == 20
    assert body["next"] is not None


def test_timetable_services_are_read_only(
    api_client: APIClient,
    viewer: User,
    administrator: User,
    berlin: Station,
    hamburg: Station,
) -> None:
    synchronize_timetables(actor=administrator, provider=MockRailwayProvider())
    api_client.force_login(viewer)
    listing = api_client.get("/api/v1/services/")
    assert listing.status_code == 200
    assert listing.json()["count"] == 2
    service_id = listing.json()["results"][0]["id"]
    detail = api_client.get(f"/api/v1/services/{service_id}/")
    assert detail.status_code == 200
    stops = api_client.get(f"/api/v1/services/{service_id}/stops/")
    assert stops.status_code == 200
    assert len(stops.json()) == 2
    assert api_client.post("/api/v1/services/", {}, format="json").status_code == 405
    assert TrainService.objects.count() == 2


def test_openapi_schema_requires_authentication(
    api_client: APIClient,
    administrator: User,
) -> None:
    assert api_client.get("/api/schema/").status_code == 401
    api_client.force_login(administrator)
    schema = api_client.get("/api/schema/")
    assert schema.status_code == 200
    body = schema.content.decode("utf-8").lower()
    assert "openapi" in body
    assert "stations" in body
    assert "incidents" in body
    assert "services" in body


def test_api_post_requires_csrf(administrator: User, berlin: Station) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(administrator)
    response = client.post(
        "/api/v1/incidents/",
        data={
            "title": "CSRF",
            "description": "Should fail.",
            "station": str(berlin.pk),
            "category": "other",
            "severity": "low",
        },
        content_type="application/json",
    )
    assert response.status_code == 403
    assert not Incident.objects.exists()
