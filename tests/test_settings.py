from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from config.settings.validation import (
    merge_local_csrf_trusted_origins,
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
    auth = "django.contrib.auth.middleware.AuthenticationMiddleware"
    active = "apps.accounts.middleware.ActiveUserSessionMiddleware"
    login = "django.contrib.auth.middleware.LoginRequiredMiddleware"
    assert middleware.index(active) == middleware.index(auth) + 1
    assert middleware.index(login) == middleware.index(active) + 1


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
    assert "SECURE_REDIRECT_EXEMPT" in source
    assert r"^health/?$" in source


def test_dockerfile_defaults_to_production_settings() -> None:
    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")
    assert "DJANGO_SETTINGS_MODULE=config.settings.production" in dockerfile
    assert "DJANGO_SETTINGS_MODULE=config.settings.development" not in dockerfile


def test_compose_overrides_development_settings() -> None:
    compose = (Path(__file__).resolve().parents[1] / "compose.yaml").read_text(encoding="utf-8")
    assert "DJANGO_SETTINGS_MODULE: config.settings.development" in compose
    assert "APP_PUBLISH_PORT: ${APP_PUBLISH_PORT:-8000}" in compose


def test_env_example_includes_csrf_origins_for_8000_and_8001() -> None:
    text = (Path(__file__).resolve().parents[1] / ".env.example").read_text(encoding="utf-8")
    assert "http://localhost:8000" in text
    assert "http://127.0.0.1:8000" in text
    assert "http://localhost:8001" in text
    assert "http://127.0.0.1:8001" in text
    assert "APP_PUBLISH_PORT" in text


def test_merge_local_csrf_trusted_origins_includes_publish_port() -> None:
    merged = merge_local_csrf_trusted_origins(
        ["http://localhost:8000"],
        app_publish_port="8001",
    )
    assert "http://localhost:8000" in merged
    assert "http://127.0.0.1:8000" in merged
    assert "http://localhost:8001" in merged
    assert "http://127.0.0.1:8001" in merged
