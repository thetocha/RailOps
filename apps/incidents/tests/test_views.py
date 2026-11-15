from __future__ import annotations

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.incidents.models import Incident, IncidentEvent
from apps.incidents.tests.conftest import redirect_location
from apps.infrastructure.models import RailwayLine, Station

pytestmark = pytest.mark.django_db


def _create_payload(berlin: Station, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Weather delay",
        "description": "Ice on the switches.",
        "station": str(berlin.pk),
        "category": Incident.Category.WEATHER,
        "severity": Incident.Severity.MEDIUM,
    }
    payload.update(overrides)
    return payload


def test_anonymous_users_are_redirected(client: Client, open_incident: Incident) -> None:
    listing = client.get("/incidents/")
    assert listing.status_code == 302
    assert "/accounts/login/" in redirect_location(listing)
    detail = client.get(f"/incidents/{open_incident.pk}/")
    assert detail.status_code == 302


def test_viewer_can_view_but_cannot_mutate(
    client: Client,
    viewer: User,
    berlin: Station,
    open_incident: Incident,
) -> None:
    client.force_login(viewer)
    listing = client.get("/incidents/")
    assert listing.status_code == 200
    assert b"Signal failure at Berlin" in listing.content
    assert b"Register incident" not in listing.content
    assert client.get(f"/incidents/{open_incident.pk}/").status_code == 200
    assert client.get("/incidents/create/").status_code == 403
    assert client.post("/incidents/create/", _create_payload(berlin)).status_code == 403
    assert not Incident.objects.filter(title="Weather delay").exists()
    transition = client.post(
        f"/incidents/{open_incident.pk}/transition/",
        {"new_status": Incident.Status.IN_PROGRESS},
    )
    assert transition.status_code == 403
    open_incident.refresh_from_db()
    assert open_incident.status == Incident.Status.OPEN


def test_dispatcher_registers_assigns_and_transitions(
    client: Client,
    dispatcher: User,
    administrator: User,
    berlin: Station,
    berlin_hamburg: RailwayLine,
) -> None:
    client.force_login(dispatcher)
    created = client.post(
        "/incidents/create/",
        _create_payload(berlin, railway_line=str(berlin_hamburg.pk)),
    )
    assert created.status_code == 302
    incident = Incident.objects.get(title="Weather delay")
    assert incident.reporter_id == dispatcher.pk
    assert incident.events.filter(event_type=IncidentEvent.EventType.CREATED).exists()

    assigned = client.post(
        f"/incidents/{incident.pk}/assign/",
        {"assigned_to": str(administrator.pk), "comment": "Please review."},
    )
    assert assigned.status_code == 302
    incident.refresh_from_db()
    assert incident.assigned_to_id == administrator.pk

    severity = client.post(
        f"/incidents/{incident.pk}/severity/",
        {"severity": Incident.Severity.CRITICAL},
    )
    assert severity.status_code == 302
    incident.refresh_from_db()
    assert incident.severity == Incident.Severity.CRITICAL

    moved = client.post(
        f"/incidents/{incident.pk}/transition/",
        {"new_status": Incident.Status.IN_PROGRESS, "comment": "On site."},
    )
    assert moved.status_code == 302
    incident.refresh_from_db()
    assert incident.status == Incident.Status.IN_PROGRESS
    detail = client.get(f"/incidents/{incident.pk}/")
    assert b"Status changed" in detail.content
    assert b"Please review." in detail.content


def test_invalid_transition_post_does_not_change_status(
    client: Client,
    dispatcher: User,
    open_incident: Incident,
) -> None:
    client.force_login(dispatcher)
    response = client.post(
        f"/incidents/{open_incident.pk}/transition/",
        {"new_status": Incident.Status.CLOSED},
    )
    assert response.status_code == 302
    open_incident.refresh_from_db()
    assert open_incident.status == Incident.Status.OPEN


def test_incident_list_search_and_filters(
    client: Client,
    dispatcher: User,
    berlin: Station,
    hamburg: Station,
) -> None:
    client.force_login(dispatcher)
    create_incident = Incident.objects.create
    first = create_incident(
        title="Ice at Berlin",
        description="Switches frozen.",
        station=berlin,
        category=Incident.Category.WEATHER,
        severity=Incident.Severity.HIGH,
        reporter=dispatcher,
        status=Incident.Status.OPEN,
    )
    IncidentEvent.objects.create(
        incident=first,
        actor=dispatcher,
        event_type=IncidentEvent.EventType.CREATED,
        new_status=Incident.Status.OPEN,
    )
    create_incident(
        title="Delay at Hamburg",
        description="Late departure.",
        station=hamburg,
        category=Incident.Category.OPERATIONAL_DELAY,
        severity=Incident.Severity.LOW,
        reporter=dispatcher,
        status=Incident.Status.IN_PROGRESS,
    )
    search = client.get("/incidents/?q=Ice")
    assert b"Ice at Berlin" in search.content
    assert b"Delay at Hamburg" not in search.content
    filtered = client.get("/incidents/?status=in_progress")
    assert b"Delay at Hamburg" in filtered.content
    assert b"Ice at Berlin" not in filtered.content
    by_station = client.get(f"/incidents/?station={berlin.pk}")
    assert b"Ice at Berlin" in by_station.content
    assert b"Delay at Hamburg" not in by_station.content


def test_csrf_required_to_register_incident(
    dispatcher: User,
    berlin: Station,
) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(dispatcher)
    response = client.post("/incidents/create/", _create_payload(berlin))
    assert response.status_code == 403
    assert not Incident.objects.filter(title="Weather delay").exists()
