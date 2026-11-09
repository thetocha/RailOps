from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.db.utils import OperationalError
from django.test import Client, override_settings


@pytest.mark.django_db
def test_health_ok(client: Client) -> None:
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_unavailable_when_database_fails(client: Client) -> None:
    with patch("config.health.connection") as mock_connection:
        mock_connection.cursor.side_effect = OperationalError("connection refused")
        response = client.get("/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert b"refused" not in response.content
    assert b"Traceback" not in response.content


@pytest.mark.django_db
def test_health_is_exempt_from_ssl_redirect() -> None:
    with override_settings(
        SECURE_SSL_REDIRECT=True,
        SECURE_REDIRECT_EXEMPT=[r"^health/?$"],
    ):
        client = Client()
        health = client.get("/health/")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}
        login = client.get("/accounts/login/")
        assert login.status_code == 301
        assert login["Location"].startswith("https://")


def test_health_does_not_leak_exception_details(client: Client) -> None:
    cursor = MagicMock()
    cursor.execute.side_effect = RuntimeError("dsn=postgres://railops:secret@db/railops")
    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cursor
    cursor_cm.__exit__.return_value = False

    with patch("config.health.connection") as mock_connection:
        mock_connection.cursor.return_value = cursor_cm
        response = client.get("/health/")

    assert response.status_code == 503
    body = response.content.decode()
    assert "secret" not in body
    assert "postgres://" not in body
