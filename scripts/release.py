"""Production release step: wait for the database, migrate, collect static files.

App workers must not import this module or run migrations on startup.
"""

from __future__ import annotations

import logging
import os

import django
from django.core.management import call_command
from scripts.wait_for_db import main as wait_for_database

logger = logging.getLogger(__name__)


def run_release() -> int:
    if wait_for_database() != 0:
        return 1
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
    django.setup()
    logger.info("Applying database migrations")
    call_command("migrate", interactive=False)
    logger.info("Collecting static files")
    call_command("collectstatic", interactive=False, verbosity=1)
    logger.info("Release step finished")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    return run_release()


if __name__ == "__main__":
    raise SystemExit(main())
