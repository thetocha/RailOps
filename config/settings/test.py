"""Test settings. Always use PostGIS — never SQLite."""

from config.settings.base import *  # noqa: F403
from config.settings.base import DATABASES, env

DEBUG = False
SECRET_KEY = env(
    "SECRET_KEY",
    default="test-insecure-secret-key-for-automated-tests-only",
)
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    }
}
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = False
