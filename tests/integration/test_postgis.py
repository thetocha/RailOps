from __future__ import annotations

import pytest
from django.db import connection

pytestmark = pytest.mark.django_db


def test_postgis_extension_is_available() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT PostGIS_Version();")
        row = cursor.fetchone()
    assert row is not None
    assert row[0]
