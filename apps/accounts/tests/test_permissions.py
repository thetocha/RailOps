from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client

from apps.accounts.models import User
from apps.accounts.permissions import (
    GROUP_ADMINISTRATOR,
    GROUP_DISPATCHER,
    GROUP_VIEWER,
    can_access_dashboard,
    can_change_operations,
    can_manage_users,
    can_view_operations,
    ensure_role_groups,
)

pytestmark = pytest.mark.django_db


def test_role_groups_receive_catalog_permissions(role_groups: dict[str, Group]) -> None:
    administrator = role_groups[GROUP_ADMINISTRATOR]
    dispatcher = role_groups[GROUP_DISPATCHER]
    viewer = role_groups[GROUP_VIEWER]

    assert administrator.permissions.filter(codename="manage_users").exists()
    assert administrator.permissions.filter(codename="change_operations").exists()
    assert dispatcher.permissions.filter(codename="change_operations").exists()
    assert not dispatcher.permissions.filter(codename="manage_users").exists()
    assert viewer.permissions.filter(codename="view_operations").exists()
    assert not viewer.permissions.filter(codename="change_operations").exists()
    assert not viewer.permissions.filter(codename="manage_users").exists()
    assert not administrator.permissions.filter(codename="delete_user").exists()


def test_ensure_role_groups_is_idempotent_and_preserves_foreign_permissions(
    role_groups: dict[str, Group],
) -> None:
    dispatcher = role_groups[GROUP_DISPATCHER]
    extra = Permission.objects.get(codename="view_group")
    dispatcher.permissions.add(extra)
    ensure_role_groups()
    dispatcher.refresh_from_db()
    assert dispatcher.permissions.filter(pk=extra.pk).exists()
    assert not dispatcher.permissions.filter(codename="manage_users").exists()


def test_ensure_role_groups_revokes_stale_managed_permissions(
    role_groups: dict[str, Group],
) -> None:
    viewer = role_groups[GROUP_VIEWER]
    manage = Permission.objects.get(content_type__app_label="accounts", codename="manage_users")
    viewer.permissions.add(manage)
    ensure_role_groups()
    assert not viewer.permissions.filter(pk=manage.pk).exists()


def test_permission_helpers_follow_permissions_not_usernames(
    administrator: User,
    dispatcher: User,
    viewer: User,
) -> None:
    assert can_manage_users(administrator)
    assert can_access_dashboard(administrator)
    assert can_change_operations(administrator)
    assert not can_manage_users(dispatcher)
    assert can_change_operations(dispatcher)
    assert can_view_operations(viewer)
    assert not can_change_operations(viewer)
    assert not can_manage_users(viewer)


def test_views_do_not_hardcode_role_group_names() -> None:
    source = Path(__file__).resolve().parents[1] / "views.py"
    text = source.read_text(encoding="utf-8")
    for role_name in (GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER):
        assert role_name not in text


def test_direct_permission_grants_user_management_without_administrator_group(
    client: Client,
    viewer: User,
    manage_users_permission: Permission,
) -> None:
    viewer.user_permissions.add(manage_users_permission)
    client.force_login(viewer)
    response = client.get("/accounts/users/")
    assert response.status_code == 200


def test_content_type_for_custom_permissions_is_accounts_user() -> None:
    content_type = ContentType.objects.get(app_label="accounts", model="user")
    assert Permission.objects.filter(
        content_type=content_type,
        codename="access_dashboard",
    ).exists()
