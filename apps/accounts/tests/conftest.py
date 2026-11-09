from __future__ import annotations

import pytest
from django.contrib.auth.models import Group, Permission

from apps.accounts.models import User
from apps.accounts.permissions import (
    GROUP_ADMINISTRATOR,
    GROUP_DISPATCHER,
    GROUP_VIEWER,
    ROLE_GROUP_NAMES,
    ensure_role_groups,
)
from apps.accounts.services import sync_staff_flag

TEST_PASSWORD = "a-strong-test-password-123"


def redirect_location(response: object) -> str:
    headers = getattr(response, "headers", None)
    if headers is None:
        return ""
    return str(headers.get("Location", ""))


@pytest.fixture
def role_groups(db: None) -> dict[str, Group]:
    ensure_role_groups()
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
    return _user_with_group(
        username="dispatcher_user",
        group=role_groups[GROUP_DISPATCHER],
    )


@pytest.fixture
def viewer(role_groups: dict[str, Group]) -> User:
    return _user_with_group(username="viewer_user", group=role_groups[GROUP_VIEWER])


@pytest.fixture
def manage_users_permission(role_groups: dict[str, Group]) -> Permission:
    return Permission.objects.get(
        content_type__app_label="accounts",
        codename="manage_users",
    )
