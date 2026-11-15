"""Provider adapter protocol. Implementations must return already-validated models."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from apps.integrations.providers.schemas import ProviderService


class RailwayProvider(Protocol):
    name: str

    def fetch_services(self, *, service_date: date | None = None) -> list[ProviderService]:
        """Return validated services. Must not persist. Must not log secrets."""
        ...
