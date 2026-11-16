"""Settings used only while collecting static files during the image build.

Runtime processes must use ``config.settings.production``. This module avoids
production secret checks so collectstatic can run with dummy build-time values
that are not baked into the container environment.
"""

from config.settings.base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "collectstatic-build-placeholder-not-used-at-runtime-xxxxx"  # nosec B105
ALLOWED_HOSTS = ["localhost"]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
