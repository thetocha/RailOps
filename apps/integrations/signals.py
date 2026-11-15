"""Integration signal handlers. Failures are not swallowed."""

from __future__ import annotations

from typing import Any


def seed_integration_permissions_on_migrate(**_kwargs: Any) -> None:
    from apps.integrations.permissions import ensure_integration_permissions

    ensure_integration_permissions()
