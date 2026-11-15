"""Timetable signal handlers. Failures are not swallowed."""

from __future__ import annotations

from typing import Any


def seed_timetable_permissions_on_migrate(**_kwargs: Any) -> None:
    from apps.timetables.permissions import ensure_timetable_permissions

    ensure_timetable_permissions()
