"""HTTPX client for a licensed timetable JSON endpoint.

This is not a national railway API. It speaks the RailOps provider JSON
schema against ``EXTERNAL_RAILWAY_API_URL`` when that URL is configured.
Tests must use a mock transport, never the public internet.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from datetime import date

import httpx
from pydantic import TypeAdapter, ValidationError

from apps.integrations.providers.schemas import ProviderService

logger = logging.getLogger(__name__)

TRANSIENT_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
MAX_RETRIES = 3
CONNECT_TIMEOUT_SECONDS = 5.0
READ_TIMEOUT_SECONDS = 10.0


def _retry_after_seconds(headers: Mapping[str, str], fallback: float) -> float:
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is None:
        return fallback
    try:
        return max(float(raw), 0.0)
    except ValueError:
        return fallback


class ExternalRailwayAPIClient:
    name = "http"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str = "",
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not base_url:
            raise ValueError("EXTERNAL_RAILWAY_API_URL is not configured.")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport
        self._sleep = sleep

    def fetch_services(self, *, service_date: date | None = None) -> list[ProviderService]:
        params: dict[str, str] = {}
        if service_date is not None:
            params["service_date"] = service_date.isoformat()
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        timeout = httpx.Timeout(
            connect=CONNECT_TIMEOUT_SECONDS,
            read=READ_TIMEOUT_SECONDS,
            write=READ_TIMEOUT_SECONDS,
            pool=CONNECT_TIMEOUT_SECONDS,
        )
        url = f"{self._base_url}/services"
        with httpx.Client(timeout=timeout, transport=self._transport) as client:
            payload = self._get_json(client, url=url, headers=headers, params=params)
        try:
            return TypeAdapter(list[ProviderService]).validate_python(payload)
        except ValidationError as exc:
            logger.warning("Provider payload failed validation error_count=%s", exc.error_count())
            raise ValueError("External timetable payload failed validation.") from exc

    def _get_json(
        self,
        client: httpx.Client,
        *,
        url: str,
        headers: dict[str, str],
        params: dict[str, str],
    ) -> object:
        delay = 0.5
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = client.get(url, headers=headers, params=params)
            except httpx.RequestError as exc:
                last_error = exc
                logger.warning(
                    "Timetable HTTP transport error attempt=%s error=%s",
                    attempt + 1,
                    exc.__class__.__name__,
                )
                if attempt == MAX_RETRIES:
                    raise
                self._sleep(delay)
                delay *= 2
                continue
            if response.status_code in TRANSIENT_STATUS_CODES and attempt < MAX_RETRIES:
                wait = _retry_after_seconds(response.headers, delay)
                logger.warning(
                    "Timetable HTTP transient status=%s attempt=%s retry_after=%s",
                    response.status_code,
                    attempt + 1,
                    wait,
                )
                self._sleep(wait)
                delay *= 2
                continue
            if response.status_code >= 400:
                logger.warning("Timetable HTTP error status=%s", response.status_code)
                response.raise_for_status()
            return response.json()
        if last_error is not None:
            raise last_error
        raise RuntimeError("Timetable HTTP client exhausted retries.")
