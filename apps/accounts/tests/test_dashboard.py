from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.gis.geos import Point
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.permissions import (
    GROUP_DISPATCHER,
    GROUP_VIEWER,
    ensure_role_groups,
)
from apps.accounts.services import sync_staff_flag
from apps.accounts.tests.conftest import TEST_PASSWORD
from apps.analytics.permissions import ensure_analytics_permissions
from apps.incidents.models import Incident
from apps.incidents.permissions import ensure_incident_permissions
from apps.incidents.services import create_incident
from apps.infrastructure.models import Station
from apps.infrastructure.permissions import ensure_infrastructure_permissions
from apps.timetables.models import TrainService
from apps.timetables.permissions import ensure_timetable_permissions
from apps.timetables.services import upsert_scheduled_stop, upsert_train_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def operational_groups(db: None) -> None:
    ensure_role_groups()
    ensure_infrastructure_permissions()
    ensure_incident_permissions()
    ensure_timetable_permissions()
    ensure_analytics_permissions()


def _user(username: str, group_name: str) -> User:
    from django.contrib.auth.models import Group

    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=TEST_PASSWORD,
    )
    user.groups.add(Group.objects.get(name=group_name))
    sync_staff_flag(user)
    user.refresh_from_db()
    return user


@pytest.fixture
def viewer(operational_groups: None) -> User:
    return _user("dash_viewer", GROUP_VIEWER)


@pytest.fixture
def dispatcher(operational_groups: None) -> User:
    return _user("dash_dispatcher", GROUP_DISPATCHER)


@pytest.fixture
def berlin(db: None) -> Station:
    return Station.objects.create(
        name="Berlin Hauptbahnhof",
        code="BHF",
        city="Berlin",
        location=Point(13.3695, 52.5255, srid=4326),
    )


@pytest.fixture
def hamburg(db: None) -> Station:
    return Station.objects.create(
        name="Hamburg Hauptbahnhof",
        code="HH",
        city="Hamburg",
        location=Point(10.0069, 53.5528, srid=4326),
    )


def test_empty_dashboard_renders_zero_metrics_and_empty_states(
    client: Client,
    viewer: User,
) -> None:
    client.force_login(viewer)
    response = client.get("/")
    assert response.status_code == 200
    assert b'data-testid="metric-total-incidents"' in response.content
    assert b">0</div>" in response.content
    assert b"No incidents have been registered yet." in response.content
    assert b"No active stations to show on the map." in response.content
    assert b"No train services have been imported yet." in response.content
    assert b"station-map-data" in response.content
    assert response.context["overview"].incidents.total == 0
    assert response.context["station_markers"] == []


def test_dashboard_metrics_come_from_persisted_records(
    client: Client,
    viewer: User,
    dispatcher: User,
    berlin: Station,
    hamburg: Station,
) -> None:
    incident = create_incident(
        actor=dispatcher,
        title="Signal failure",
        description="Home signal stuck.",
        station=berlin,
        category=Incident.Category.SIGNAL_FAILURE,
        severity=Incident.Severity.CRITICAL,
    )
    Incident.objects.filter(pk=incident.pk).update(
        reported_at=datetime.now(tz=UTC) - timedelta(hours=1),
    )
    day = timezone.localdate()
    scheduled = datetime.now(tz=UTC).replace(hour=8, minute=0, second=0, microsecond=0)
    service, _ = upsert_train_service(
        external_id="ICE-DASH",
        train_number="ICE 9",
        origin=berlin,
        destination=hamburg,
        service_date=day,
        source=TrainService.Source.MOCK,
    )
    upsert_scheduled_stop(
        train_service=service,
        station=hamburg,
        stop_sequence=1,
        scheduled_arrival=scheduled,
        scheduled_departure=None,
        actual_arrival=scheduled + timedelta(minutes=12),
        actual_departure=None,
    )
    client.force_login(viewer)
    response = client.get("/")
    assert response.status_code == 200
    assert response.context["overview"].incidents.total == 1
    assert response.context["overview"].incidents.open_count == 1
    assert response.context["critical_incidents"] == 1
    assert response.context["overview"].delays.delayed_services == 1
    assert b"Signal failure" in response.content
    assert b"ICE 9" in response.content
    assert b"BHF" in response.content
    markers = response.context["station_markers"]
    assert {marker["code"] for marker in markers} == {"BHF", "HH"}
    assert any(marker["latitude"] == pytest.approx(52.5255) for marker in markers)


def test_station_detail_includes_map_payload(
    client: Client,
    viewer: User,
    berlin: Station,
) -> None:
    client.force_login(viewer)
    response = client.get(f"/stations/{berlin.pk}/")
    assert response.status_code == 200
    markers = response.context["station_markers"]
    assert len(markers) == 1
    assert markers[0]["code"] == "BHF"
    assert b"station-map-data" in response.content
    assert b"52.525500" in response.content or b"52.5255" in response.content


def test_dashboard_does_not_depend_on_javascript_for_metrics(
    client: Client,
    viewer: User,
    dispatcher: User,
    berlin: Station,
) -> None:
    create_incident(
        actor=dispatcher,
        title="Weather delay",
        description="Ice on the line.",
        station=berlin,
        category=Incident.Category.WEATHER,
        severity=Incident.Severity.HIGH,
    )
    client.force_login(viewer)
    response = client.get("/")
    assert b"<canvas" in response.content
    assert b"High" in response.content
    assert b"Weather delay" in response.content
