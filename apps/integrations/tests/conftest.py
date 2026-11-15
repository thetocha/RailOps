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
from apps.infrastructure.models import Station
from apps.infrastructure.permissions import ensure_infrastructure_permissions
from apps.integrations.permissions import ensure_integration_permissions
from apps.timetables.permissions import ensure_timetable_permissions

TEST_PASSWORD = "a-strong-test-password-123"


@pytest.fixture
def role_groups(db: None) -> dict[str, Group]:
    ensure_role_groups()
    ensure_infrastructure_permissions()
    ensure_timetable_permissions()
    ensure_integration_permissions()
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
    return _user_with_group(username="admin_user", group=role_groups[GROUP_ADMINISTRATOR])


@pytest.fixture
def dispatcher(role_groups: dict[str, Group]) -> User:
    return _user_with_group(username="dispatcher_user", group=role_groups[GROUP_DISPATCHER])


@pytest.fixture
def viewer(role_groups: dict[str, Group]) -> User:
    return _user_with_group(username="viewer_user", group=role_groups[GROUP_VIEWER])


@pytest.fixture
def berlin_hamburg(db: None) -> tuple[Station, Station]:
    berlin = Station.objects.create(
        name="Berlin Hauptbahnhof",
        code="BHF",
        city="Berlin",
        location=Point(13.3695, 52.5255, srid=4326),
    )
    hamburg = Station.objects.create(
        name="Hamburg Hauptbahnhof",
        code="HH",
        city="Hamburg",
        location=Point(10.0069, 53.5528, srid=4326),
    )
    return berlin, hamburg
