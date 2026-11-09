"""Local development settings."""

from config.settings.base import *  # noqa: F403
from config.settings.base import CSRF_TRUSTED_ORIGINS, env
from config.settings.validation import merge_local_csrf_trusted_origins

DEBUG = env.bool("DEBUG", default=True)
SECRET_KEY = env("SECRET_KEY", default="replace-me")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    }
}
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

APP_PUBLISH_PORT = env("APP_PUBLISH_PORT", default="8000")
CSRF_TRUSTED_ORIGINS = merge_local_csrf_trusted_origins(
    list(CSRF_TRUSTED_ORIGINS),
    app_publish_port=APP_PUBLISH_PORT,
)
