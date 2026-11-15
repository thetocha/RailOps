"""Infrastructure signal handlers. Failures are not swallowed."""

from __future__ import annotations

from typing import Any


def seed_infrastructure_permissions_on_migrate(**_kwargs: Any) -> None:
    from apps.infrastructure.permissions import ensure_infrastructure_permissions

    ensure_infrastructure_permissions()
