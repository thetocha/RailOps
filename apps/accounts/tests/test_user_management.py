from __future__ import annotations

import pytest
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import Group
from django.test import Client

from apps.accounts.forms import UserCreateForm
from apps.accounts.models import User
from apps.accounts.permissions import GROUP_DISPATCHER
from apps.accounts.services import create_user
from apps.accounts.tests.conftest import redirect_location

pytestmark = pytest.mark.django_db

CREATED_PASSWORD = "created-user-strong-pass-123"


def _create_payload(role_groups: dict[str, Group], username: str = "newops") -> dict[str, object]:
    return {
        "username": username,
        "email": f"{username}@example.com",
        "first_name": "New",
        "last_name": "Operator",
        "password1": CREATED_PASSWORD,
        "password2": CREATED_PASSWORD,
        "is_active": "on",
        "groups": [role_groups[GROUP_DISPATCHER].pk],
    }


def test_viewer_cannot_create_or_update_users(
    client: Client,
    viewer: User,
    administrator: User,
    role_groups: dict[str, Group],
) -> None:
    client.force_login(viewer)
    assert client.get("/accounts/users/").status_code == 403
    assert client.get("/accounts/users/create/").status_code == 403
    create_response = client.post("/accounts/users/create/", _create_payload(role_groups))
    assert create_response.status_code == 403
    assert not User.objects.filter(username="newops").exists()

    edit_url = f"/accounts/users/{administrator.pk}/edit/"
    assert client.get(edit_url).status_code == 403
    update_response = client.post(
        edit_url,
        {
            "username": administrator.username,
            "email": "hacked@example.com",
            "first_name": "",
            "last_name": "",
            "is_active": "on",
            "groups": [role_groups[GROUP_DISPATCHER].pk],
        },
    )
    assert update_response.status_code == 403
    administrator.refresh_from_db()
    assert administrator.email != "hacked@example.com"


def test_dispatcher_cannot_manage_users(
    client: Client,
    dispatcher: User,
    role_groups: dict[str, Group],
) -> None:
    client.force_login(dispatcher)
    assert client.get("/accounts/users/").status_code == 403
    assert client.post("/accounts/users/create/", _create_payload(role_groups)).status_code == 403
    assert not User.objects.filter(username="newops").exists()
    admin_login = client.get("/admin/")
    assert admin_login.status_code == 302
    assert "/admin/login/" in redirect_location(admin_login)


def test_administrator_can_create_user_and_assign_group(
    client: Client,
    administrator: User,
    role_groups: dict[str, Group],
) -> None:
    client.force_login(administrator)
    list_response = client.get("/accounts/users/")
    assert list_response.status_code == 200
    assert administrator.password.encode() not in list_response.content

    response = client.post("/accounts/users/create/", _create_payload(role_groups))
    assert response.status_code == 302
    created = User.objects.get(username="newops")
    assert created.email == "newops@example.com"
    assert created.check_password(CREATED_PASSWORD)
    identify_hasher(created.password)
    assert created.password != CREATED_PASSWORD
    assert created.groups.filter(name=GROUP_DISPATCHER).exists()
    assert not created.is_staff


def test_administrator_user_edit_does_not_display_password_hash(
    client: Client,
    administrator: User,
) -> None:
    client.force_login(administrator)
    response = client.get(f"/accounts/users/{administrator.pk}/edit/")
    assert response.status_code == 200
    assert administrator.password.encode() not in response.content
    assert b"md5$" not in response.content
    assert b"pbkdf2" not in response.content


def test_user_form_role_checkboxes_do_not_use_collapsed_wrapper(
    client: Client,
    administrator: User,
) -> None:
    client.force_login(administrator)
    response = client.get("/accounts/users/create/")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="id_groups"' not in html or 'id="id_groups" class="form-check-input"' not in html
    assert html.count('name="groups"') == 3
    assert "Administrator" in html
    assert "Dispatcher" in html
    assert "Viewer" in html
    assert 'class="form-check-input"' in html
    assert "railops-choice-list" in html
    assert html.rindex("Viewer") < html.index(">Save<")
    assert html.rindex("Viewer") < html.index(">Cancel<")


def test_create_user_service_hashes_password(
    administrator: User,
    role_groups: dict[str, Group],
) -> None:
    created = create_user(
        actor=administrator,
        username="serviceops",
        email="serviceops@example.com",
        password=CREATED_PASSWORD,
        groups=[role_groups[GROUP_DISPATCHER]],
    )
    assert created.password != CREATED_PASSWORD
    identify_hasher(created.password)
    assert created.check_password(CREATED_PASSWORD)


def test_administrator_can_deactivate_another_user(
    client: Client,
    administrator: User,
    dispatcher: User,
) -> None:
    client.force_login(administrator)
    response = client.post(f"/accounts/users/{dispatcher.pk}/deactivate/")
    assert response.status_code == 302
    dispatcher.refresh_from_db()
    assert dispatcher.is_active is False


def test_user_cannot_deactivate_self(
    client: Client,
    administrator: User,
) -> None:
    client.force_login(administrator)
    response = client.post(f"/accounts/users/{administrator.pk}/deactivate/", follow=True)
    assert response.status_code == 200
    administrator.refresh_from_db()
    assert administrator.is_active is True


def test_user_create_form_rejects_duplicate_email(
    dispatcher: User,
    role_groups: dict[str, Group],
) -> None:
    form = UserCreateForm(
        data={
            "username": "duplicate-mail",
            "email": dispatcher.email,
            "first_name": "",
            "last_name": "",
            "password1": CREATED_PASSWORD,
            "password2": CREATED_PASSWORD,
            "is_active": "on",
            "groups": [role_groups[GROUP_DISPATCHER].pk],
        }
    )
    assert not form.is_valid()
    assert "email" in form.errors


def test_user_create_post_without_csrf_is_rejected(administrator: User) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(administrator)
    response = client.post(
        "/accounts/users/create/",
        {
            "username": "csrfprobe",
            "email": "csrfprobe@example.com",
            "password1": CREATED_PASSWORD,
            "password2": CREATED_PASSWORD,
        },
    )
    assert response.status_code == 403
    assert not User.objects.filter(username="csrfprobe").exists()
