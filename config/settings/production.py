"""Production settings with fail-closed security defaults."""

from config.settings.base import *  # noqa: F403
from config.settings.base import DATABASES, env
from config.settings.validation import (
    validate_production_allowed_hosts,
    validate_production_database_password,
    validate_production_debug,
    validate_production_secret_key,
)

DEBUG = False
validate_production_debug(DEBUG)

SECRET_KEY = env("SECRET_KEY")
validate_production_secret_key(SECRET_KEY)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
validate_production_allowed_hosts(ALLOWED_HOSTS)

database_password = env("DB_PASSWORD")
validate_production_database_password(database_password)
DATABASES["default"]["PASSWORD"] = database_password

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [
        f"https://{host}" for host in ALLOWED_HOSTS if host not in {"localhost", "127.0.0.1"}
    ]

MAILERS = {
    "default": {
        "BACKEND": env(
            "EMAIL_BACKEND",
            default="django.core.mail.backends.smtp.EmailBackend",
        ),
        "OPTIONS": {
            "host": env("EMAIL_HOST", default="localhost"),
            "port": env.int("EMAIL_PORT", default=587),
            "username": env("EMAIL_HOST_USER", default=""),
            "password": env("EMAIL_HOST_PASSWORD", default=""),
            "use_tls": env.bool("EMAIL_USE_TLS", default=True),
        },
    }
}
