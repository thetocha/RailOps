from __future__ import annotations

import pytest
from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session
from django.test import Client

from apps.accounts.models import User
from apps.accounts.services import update_user
from apps.accounts.tests.conftest import redirect_location

pytestmark = pytest.mark.django_db


def _session_user_ids() -> set[str]:
    user_ids: set[str] = set()
    for session in Session.objects.iterator():
        data = session.get_decoded()
        stored = data.get(SESSION_KEY)
        if stored is not None:
            user_ids.add(str(stored))
    return user_ids


def test_deactivate_invalidates_session_and_redirects_to_login(
    administrator: User,
    dispatcher: User,
) -> None:
    dispatcher_client = Client()
    dispatcher_client.force_login(dispatcher)
    assert dispatcher_client.get("/").status_code == 200
    assert dispatcher_client.get("/accounts/password-change/").status_code == 200
    assert str(dispatcher.pk) in _session_user_ids()

    admin_client = Client()
    admin_client.force_login(administrator)
    response = admin_client.post(f"/accounts/users/{dispatcher.pk}/deactivate/")
    assert response.status_code == 302

    dispatcher.refresh_from_db()
    assert dispatcher.is_active is False
    assert str(dispatcher.pk) not in _session_user_ids()

    dashboard = dispatcher_client.get("/")
    assert dashboard.status_code == 302
    assert "/accounts/login/" in redirect_location(dashboard)

    password_change = dispatcher_client.get("/accounts/password-change/")
    assert password_change.status_code == 302
    assert "/accounts/login/" in redirect_location(password_change)


def test_update_user_inactive_invalidates_session(
    administrator: User,
    dispatcher: User,
) -> None:
    target_client = Client()
    target_client.force_login(dispatcher)
    assert target_client.get("/").status_code == 200

    update_user(
        actor=administrator,
        user=dispatcher,
        username=dispatcher.username,
        email=dispatcher.email,
        first_name=dispatcher.first_name,
        last_name=dispatcher.last_name,
        is_active=False,
        groups=list(dispatcher.groups.all()),
    )
    dispatcher.refresh_from_db()
    assert dispatcher.is_active is False
    assert str(dispatcher.pk) not in _session_user_ids()

    dashboard = target_client.get("/")
    assert dashboard.status_code == 302
    assert "/accounts/login/" in redirect_location(dashboard)


def test_middleware_logs_out_inactive_user_when_backend_still_authenticates(
    dispatcher: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher.is_active = False
    dispatcher.save(update_fields=["is_active", "updated_at"])
    monkeypatch.setattr(
        "django.contrib.auth.backends.ModelBackend.user_can_authenticate",
        lambda _self, _user: True,
    )
    client = Client()
    client.force_login(dispatcher)

    password_change = client.get("/accounts/password-change/")
    assert password_change.status_code == 302
    assert "/accounts/login/" in redirect_location(password_change)

    dashboard = client.get("/")
    assert dashboard.status_code == 302
    assert "/accounts/login/" in redirect_location(dashboard)
