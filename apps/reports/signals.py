"""Report signal handlers. Failures are not swallowed."""

from __future__ import annotations

from typing import Any


def seed_report_permissions_on_migrate(**_kwargs: Any) -> None:
    from apps.reports.permissions import ensure_report_permissions

    ensure_report_permissions()
