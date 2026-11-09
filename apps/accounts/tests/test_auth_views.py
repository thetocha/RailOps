from __future__ import annotations

import pytest
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.models import User
from apps.accounts.tests.conftest import TEST_PASSWORD, redirect_location

pytestmark = pytest.mark.django_db

NEW_PASSWORD = "a-different-strong-password-456"


def test_login_page_renders(client: Client) -> None:
    response = client.get("/accounts/login/")
    assert response.status_code == 200
    assert b"csrfmiddlewaretoken" in response.content
    assert b'type="password"' in response.content


def test_unauthenticated_users_are_redirected_from_protected_pages(client: Client) -> None:
    for path in ("/", "/accounts/users/", "/accounts/password-change/"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/accounts/login/" in redirect_location(response)


def test_login_and_logout_happy_path(client: Client, viewer: User) -> None:
    response = client.post(
        "/accounts/login/",
        {"username": viewer.username, "password": TEST_PASSWORD},
    )
    assert response.status_code == 302
    assert redirect_location(response) == "/"
    follow = client.get("/")
    assert follow.status_code == 200
    assert viewer.username.encode() in follow.content

    logout = client.post("/accounts/logout/")
    assert logout.status_code == 302
    protected = client.get("/")
    assert protected.status_code == 302
    assert "/accounts/login/" in redirect_location(protected)


def test_login_rejects_wrong_password(client: Client, viewer: User) -> None:
    response = client.post(
        "/accounts/login/",
        {"username": viewer.username, "password": "definitely-wrong-password"},
        follow=True,
    )
    assert response.status_code == 200
    assert b"Please enter a correct" in response.content


def test_login_post_without_csrf_is_rejected() -> None:
    client = Client(enforce_csrf_checks=True)
    response = client.post(
        "/accounts/login/",
        {"username": "anyone", "password": TEST_PASSWORD},
    )
    assert response.status_code == 403


def test_password_change_happy_path(client: Client, viewer: User) -> None:
    client.force_login(viewer)
    response = client.post(
        "/accounts/password-change/",
        {
            "old_password": TEST_PASSWORD,
            "new_password1": NEW_PASSWORD,
            "new_password2": NEW_PASSWORD,
        },
    )
    assert response.status_code == 302
    viewer.refresh_from_db()
    assert viewer.check_password(NEW_PASSWORD)
    identify_hasher(viewer.password)


def test_password_reset_does_not_reveal_whether_user_exists(
    client: Client,
    viewer: User,
) -> None:
    unknown = client.post("/accounts/password-reset/", {"email": "nobody@example.com"})
    known = client.post("/accounts/password-reset/", {"email": viewer.email})
    assert unknown.status_code == known.status_code == 302
    assert redirect_location(unknown) == redirect_location(known) == reverse("password_reset_done")
    done = client.get(redirect_location(known))
    assert done.status_code == 200
    assert b"nobody@example.com" not in done.content
    assert viewer.email.encode() not in done.content
    assert len(mail.outbox) == 1
    assert viewer.email in mail.outbox[0].to


def test_password_reset_confirm_sets_new_password(client: Client, viewer: User) -> None:
    uid = urlsafe_base64_encode(force_bytes(viewer.pk))
    token = default_token_generator.make_token(viewer)
    url = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    redirect = client.get(url)
    assert redirect.status_code == 302
    response = client.post(
        redirect_location(redirect),
        {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD},
    )
    assert response.status_code == 302
    viewer.refresh_from_db()
    assert viewer.check_password(NEW_PASSWORD)


def test_passwords_are_stored_with_hasher_prefix(viewer: User) -> None:
    assert viewer.password != TEST_PASSWORD
    identify_hasher(viewer.password)
    assert User.objects.get(pk=viewer.pk).password.startswith(
        ("md5$", "pbkdf2_", "argon2", "bcrypt", "scrypt")
    )


def test_health_remains_public(client: Client) -> None:
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
