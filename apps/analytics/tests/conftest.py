from __future__ import annotations

import pytest
from django.contrib.auth.models import Group
from django.contrib.gis.geos import Point

from apps.accounts.models import User
from apps.accounts.permissions import (
    GROUP_ADMINISTRATOR,
    GROUP_DISPATCHER,
    GROUP_VIEWER,
    ROLE_GROUP_NAMES,
    ensure_role_groups,
)
from apps.accounts.services import sync_staff_flag
from apps.analytics.permissions import ensure_analytics_permissions
from apps.incidents.permissions import ensure_incident_permissions
from apps.infrastructure.models import Station
from apps.infrastructure.permissions import ensure_infrastructure_permissions
from apps.timetables.permissions import ensure_timetable_permissions

TEST_PASSWORD = "a-strong-test-password-123"


def redirect_location(response: object) -> str:
    headers = getattr(response, "headers", None)
    if headers is None:
        return ""
    return str(headers.get("Location", ""))


@pytest.fixture
def role_groups(db: None) -> dict[str, Group]:
    ensure_role_groups()
    ensure_infrastructure_permissions()
    ensure_incident_permissions()
    ensure_timetable_permissions()
    ensure_analytics_permissions()
    return {group.name: group for group in Group.objects.filter(name__in=ROLE_GROUP_NAMES)}


def _user_with_group(*, username: str, group: Group) -> User:
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=TEST_PASSWORD,
    )
    user.groups.add(group)
    sync_staff_flag(user)
    user.refresh_from_db()
    return user


@pytest.fixture
def administrator(role_groups: dict[str, Group]) -> User:
    return _user_with_group(username="analytics_admin", group=role_groups[GROUP_ADMINISTRATOR])


@pytest.fixture
def dispatcher(role_groups: dict[str, Group]) -> User:
    return _user_with_group(username="analytics_dispatcher", group=role_groups[GROUP_DISPATCHER])


@pytest.fixture
def viewer(role_groups: dict[str, Group]) -> User:
    return _user_with_group(username="analytics_viewer", group=role_groups[GROUP_VIEWER])


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
