from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth.models import Group, Permission
from django.test import Client

from apps.accounts.models import User
from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER
from apps.infrastructure.models import Station
from apps.infrastructure.permissions import (
    can_manage_railway_lines,
    can_manage_stations,
    can_view_railway_lines,
    can_view_stations,
    ensure_infrastructure_permissions,
)

pytestmark = pytest.mark.django_db


def test_role_groups_receive_infrastructure_permissions(role_groups: dict[str, Group]) -> None:
    administrator = role_groups[GROUP_ADMINISTRATOR]
    dispatcher = role_groups[GROUP_DISPATCHER]
    viewer = role_groups[GROUP_VIEWER]

    assert administrator.permissions.filter(codename="add_station").exists()
    assert administrator.permissions.filter(codename="change_railwayline").exists()
    assert not administrator.permissions.filter(codename="delete_station").exists()
    assert dispatcher.permissions.filter(codename="view_station").exists()
    assert not dispatcher.permissions.filter(codename="add_station").exists()
    assert viewer.permissions.filter(codename="view_railwayline").exists()
    assert not viewer.permissions.filter(codename="change_railwayline").exists()


def test_ensure_infrastructure_permissions_is_idempotent_and_revokes_stale(
    role_groups: dict[str, Group],
) -> None:
    viewer = role_groups[GROUP_VIEWER]
    add_station = Permission.objects.get(
        content_type__app_label="infrastructure",
        codename="add_station",
    )
    viewer.permissions.add(add_station)
    ensure_infrastructure_permissions()
    ensure_infrastructure_permissions()
    assert not viewer.permissions.filter(pk=add_station.pk).exists()
    assert viewer.permissions.filter(codename="view_station").exists()


def test_helpers_follow_permissions_not_usernames(
    administrator: User,
    dispatcher: User,
    viewer: User,
) -> None:
    assert can_manage_stations(administrator)
    assert can_manage_railway_lines(administrator)
    assert can_view_stations(dispatcher)
    assert can_view_railway_lines(viewer)
    assert not can_manage_stations(dispatcher)
    assert not can_manage_stations(viewer)
    assert not can_manage_railway_lines(viewer)


def test_views_do_not_hardcode_role_group_names() -> None:
    source = Path(__file__).resolve().parents[1] / "views.py"
    text = source.read_text(encoding="utf-8")
    for role_name in (GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER):
        assert role_name not in text


def test_direct_add_station_permission_opens_create_without_administrator_group(
    client: Client,
    viewer: User,
    add_station_permission: Permission,
) -> None:
    viewer.user_permissions.add(add_station_permission)
    client.force_login(viewer)
    response = client.get("/stations/create/")
    assert response.status_code == 200


def test_station_create_requires_csrf(administrator: User) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(administrator)
    response = client.post(
        "/stations/create/",
        {
            "name": "CSRF Station",
            "code": "CSRF",
            "city": "Berlin",
            "latitude": "52.5",
            "longitude": "13.4",
            "is_active": "on",
        },
    )
    assert response.status_code == 403
    assert not Station.objects.filter(code="CSRF").exists()
