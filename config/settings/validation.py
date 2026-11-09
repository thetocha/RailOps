"""Production configuration guards.

These helpers are imported by production settings and unit-tested without
loading a full production environment.
"""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured

PLACEHOLDER_SECRET = "replace-me"  # nosec B105: sentinel rejected in production, not a credential
MIN_SECRET_KEY_LENGTH = 50


def validate_production_debug(debug: bool) -> None:
    if debug:
        raise ImproperlyConfigured("DEBUG must be False in production.")


def validate_production_secret_key(secret_key: str) -> None:
    if (
        not secret_key
        or secret_key == PLACEHOLDER_SECRET
        or len(secret_key) < MIN_SECRET_KEY_LENGTH
    ):
        raise ImproperlyConfigured(
            "SECRET_KEY must be a strong value of at least "
            f"{MIN_SECRET_KEY_LENGTH} characters and must not use the placeholder."
        )


def validate_production_allowed_hosts(allowed_hosts: list[str]) -> None:
    if not allowed_hosts:
        raise ImproperlyConfigured("ALLOWED_HOSTS must be set in production.")
    if "*" in allowed_hosts:
        raise ImproperlyConfigured("ALLOWED_HOSTS must not include '*' in production.")


def validate_production_database_password(password: str) -> None:
    if not password or password == PLACEHOLDER_SECRET:
        raise ImproperlyConfigured("DB_PASSWORD must be set to a non-placeholder value.")


def merge_local_csrf_trusted_origins(
    configured: list[str],
    *,
    app_publish_port: str | int,
    default_ports: tuple[str, ...] = ("8000",),
) -> list[str]:
    """Include localhost origins for port 8000 and the host publish port.

    Development Compose may remap the app to APP_PUBLISH_PORT (8001 on some
    workstations). CSRF checks must accept that origin as well as the default
    8000 origin so a missing .env line is not a login-breaking footgun.
    """
    origins = [origin for origin in configured if origin]
    seen = set(origins)
    ports = {str(app_publish_port), *default_ports}
    for port in sorted(ports, key=lambda value: (len(value), value)):
        for host in ("localhost", "127.0.0.1"):
            origin = f"http://{host}:{port}"
            if origin not in seen:
                origins.append(origin)
                seen.add(origin)
    return origins
