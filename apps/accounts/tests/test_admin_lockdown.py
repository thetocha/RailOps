from __future__ import annotations

import pytest
from django.contrib.auth.models import Group, Permission
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.permissions import GROUP_VIEWER
from apps.accounts.tests.conftest import TEST_PASSWORD, redirect_location

pytestmark = pytest.mark.django_db


def _staff_non_superuser() -> User:
    staff = User.objects.create_user(
        username="staffer",
        email="staffer@example.com",
        password=TEST_PASSWORD,
        is_staff=True,
        is_superuser=False,
        is_active=True,
    )
    staff.user_permissions.set(Permission.objects.all())
    return staff


def test_role_administrator_is_not_staff_and_uses_application_ui(
    client: Client,
    administrator: User,
) -> None:
    assert administrator.is_staff is False
    assert administrator.is_superuser is False
    client.force_login(administrator)
    assert client.get("/accounts/users/").status_code == 200
    admin_index = client.get("/admin/")
    assert admin_index.status_code == 302
    assert "/admin/login/" in redirect_location(admin_index)


def test_staff_non_superuser_cannot_escalate_via_admin_user_change(
    client: Client,
    viewer: User,
) -> None:
    staff = _staff_non_superuser()
    client.force_login(staff)
    change_url = reverse("admin:accounts_user_change", args=[viewer.pk])
    get_response = client.get(change_url)
    assert get_response.status_code in {403, 302}

    post_response = client.post(
        change_url,
        {
            "username": viewer.username,
            "email": viewer.email,
            "is_active": "on",
            "is_staff": "on",
            "is_superuser": "on",
        },
    )
    assert post_response.status_code in {403, 302}
    viewer.refresh_from_db()
    assert viewer.is_superuser is False
    assert viewer.is_staff is False
    assert not viewer.user_permissions.exists()


def test_staff_non_superuser_cannot_add_user_via_admin(client: Client) -> None:
    staff = _staff_non_superuser()
    client.force_login(staff)
    add_url = reverse("admin:accounts_user_add")
    get_response = client.get(add_url)
    assert get_response.status_code in {403, 302}
    post_response = client.post(
        add_url,
        {
            "username": "escalated",
            "email": "escalated@example.com",
            "password1": TEST_PASSWORD,
            "password2": TEST_PASSWORD,
            "is_active": "on",
            "is_staff": "on",
            "is_superuser": "on",
        },
    )
    assert post_response.status_code in {403, 302}
    assert not User.objects.filter(username="escalated").exists()


def test_staff_non_superuser_cannot_edit_group_permissions(
    client: Client,
    role_groups: dict[str, Group],
) -> None:
    staff = _staff_non_superuser()
    client.force_login(staff)
    viewer_group = role_groups[GROUP_VIEWER]
    manage = Permission.objects.get(content_type__app_label="accounts", codename="manage_users")
    change_url = reverse("admin:auth_group_change", args=[viewer_group.pk])
    post_response = client.post(
        change_url,
        {
            "name": viewer_group.name,
            "permissions": [manage.pk],
        },
    )
    assert post_response.status_code in {403, 302}
    assert not viewer_group.permissions.filter(pk=manage.pk).exists()


def test_superuser_can_open_admin_user_change(client: Client, viewer: User) -> None:
    superuser = User.objects.create_superuser(
        username="root",
        email="root@example.com",
        password=TEST_PASSWORD,
    )
    client.force_login(superuser)
    response = client.get(reverse("admin:accounts_user_change", args=[viewer.pk]))
    assert response.status_code == 200
