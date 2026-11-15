"""Analytics signal handlers. Failures are not swallowed."""

from __future__ import annotations

from typing import Any


def seed_analytics_permissions_on_migrate(**_kwargs: Any) -> None:
    from apps.analytics.permissions import ensure_analytics_permissions

    ensure_analytics_permissions()
