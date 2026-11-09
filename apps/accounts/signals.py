"""Accounts signal handlers. Failures are not swallowed."""

from __future__ import annotations

from typing import Any


def seed_role_groups_on_migrate(**_kwargs: Any) -> None:
    from apps.accounts.permissions import ensure_role_groups

    ensure_role_groups()
