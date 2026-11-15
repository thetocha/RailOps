"""Incident signal handlers. Failures are not swallowed."""

from __future__ import annotations

from typing import Any


def seed_incident_permissions_on_migrate(**_kwargs: Any) -> None:
    from apps.incidents.permissions import ensure_incident_permissions

    ensure_incident_permissions()
