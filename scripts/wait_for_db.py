"""Block until PostgreSQL accepts connections. Does not run migrations."""

from __future__ import annotations

import os
import sys
import time
from typing import TypedDict

import psycopg


class _ConnInfo(TypedDict):
    host: str
    port: str
    dbname: str
    user: str
    password: str
    connect_timeout: int


def main() -> int:
    attempts = int(os.environ.get("DB_WAIT_ATTEMPTS", "30"))
    delay = float(os.environ.get("DB_WAIT_DELAY", "1"))
    conninfo: _ConnInfo = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "dbname": os.environ.get("DB_NAME", "railops"),
        "user": os.environ.get("DB_USER", "railops"),
        "password": os.environ.get("DB_PASSWORD", "replace-me"),
        "connect_timeout": 3,
    }
    last_error = "unknown"
    for _ in range(attempts):
        try:
            with (
                psycopg.connect(**conninfo) as connection,
                connection.cursor() as cursor,
            ):
                cursor.execute("SELECT 1")
            return 0
        except psycopg.Error as exc:
            last_error = type(exc).__name__
            time.sleep(delay)
    print(
        f"Database not ready after {attempts} attempts ({last_error}).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
