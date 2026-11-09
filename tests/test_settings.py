from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from config.settings.validation import (
    validate_production_allowed_hosts,
    validate_production_database_password,
    validate_production_debug,
    validate_production_secret_key,
)


def test_auth_user_model_setting() -> None:
    assert settings.AUTH_USER_MODEL == "accounts.User"


def test_login_redirect_settings() -> None:
    assert settings.LOGIN_URL == "login"
    assert settings.LOGIN_REDIRECT_URL == "dashboard"
    assert settings.LOGOUT_REDIRECT_URL == "login"


def test_login_required_middleware_follows_authentication() -> None:
    middleware = list(settings.MIDDLEWARE)
    auth_index = middleware.index("django.contrib.auth.middleware.AuthenticationMiddleware")
    login_index = middleware.index("django.contrib.auth.middleware.LoginRequiredMiddleware")
    assert login_index == auth_index + 1


def test_database_engine_is_postgis() -> None:
    engine = settings.DATABASES["default"]["ENGINE"]
    assert engine == "django.contrib.gis.db.backends.postgis"
    assert "sqlite" not in engine.lower()


def test_production_rejects_debug_true() -> None:
    with pytest.raises(ImproperlyConfigured, match="DEBUG"):
        validate_production_debug(True)


def test_production_allows_debug_false() -> None:
    validate_production_debug(False)


def test_production_rejects_placeholder_secret() -> None:
    with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
        validate_production_secret_key("replace-me")


def test_production_rejects_short_secret() -> None:
    with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
        validate_production_secret_key("too-short")


def test_production_accepts_strong_secret() -> None:
    validate_production_secret_key("a" * 50)


def test_production_rejects_empty_and_wildcard_hosts() -> None:
    with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS"):
        validate_production_allowed_hosts([])
    with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS"):
        validate_production_allowed_hosts(["*"])


def test_production_rejects_placeholder_database_password() -> None:
    with pytest.raises(ImproperlyConfigured, match="DB_PASSWORD"):
        validate_production_database_password("replace-me")


def test_env_example_contains_placeholders_not_secrets() -> None:
    text = (Path(__file__).resolve().parents[1] / ".env.example").read_text(encoding="utf-8")
    assert "SECRET_KEY=replace-me" in text
    assert "DB_PASSWORD=replace-me" in text
    assert "sk_live" not in text
    assert "BEGIN " not in text


def test_production_module_uses_secure_defaults() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "config" / "settings" / "production.py"
    ).read_text(encoding="utf-8")
    assert "DEBUG = False" in source
    assert "SESSION_COOKIE_SECURE = True" in source
    assert "CSRF_COOKIE_SECURE = True" in source
    assert "SESSION_COOKIE_HTTPONLY = True" in source
    assert "SECURE_HSTS_SECONDS" in source
    assert "SECURE_SSL_REDIRECT" in source
