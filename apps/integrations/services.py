"""Timetable synchronization. Provider I/O is isolated from persistence."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.permissions import require_authenticated_user
from apps.infrastructure.models import Station
from apps.integrations.models import ExternalSyncRun
from apps.integrations.permissions import PERM_RUN_SYNC
from apps.integrations.providers.base import RailwayProvider
from apps.integrations.providers.csv import CSVRailwayProvider
from apps.integrations.providers.httpx_client import ExternalRailwayAPIClient
from apps.integrations.providers.mock import MockRailwayProvider
from apps.integrations.providers.schemas import ProviderService
from apps.timetables.models import TrainService
from apps.timetables.services import upsert_scheduled_stop, upsert_train_service

logger = logging.getLogger(__name__)

ERROR_SUMMARY_MAX = 2000


def build_provider(
    *,
    name: str,
    csv_content: str | None = None,
    csv_path: Path | None = None,
) -> RailwayProvider:
    if name == MockRailwayProvider.name:
        return MockRailwayProvider()
    if name == CSVRailwayProvider.name:
        if csv_content is not None:
            return CSVRailwayProvider(content=csv_content)
        if csv_path is not None:
            return CSVRailwayProvider.from_path(csv_path)
        raise ValidationError("CSV provider requires file content or a path.")
    if name == ExternalRailwayAPIClient.name:
        return ExternalRailwayAPIClient(
            base_url=getattr(settings, "EXTERNAL_RAILWAY_API_URL", ""),
            api_key=getattr(settings, "EXTERNAL_RAILWAY_API_KEY", ""),
        )
    raise ValidationError(f"Unknown timetable provider '{name}'.")


def _truncate_errors(errors: list[str]) -> str:
    text = " | ".join(errors)
    if len(text) > ERROR_SUMMARY_MAX:
        return text[: ERROR_SUMMARY_MAX - 3] + "..."
    return text


def _persist_service(payload: ProviderService, *, source: TrainService.Source) -> str | None:
    stations = {
        station.code: station
        for station in Station.objects.filter(
            code__in={
                payload.origin_code,
                payload.destination_code,
                *(stop.station_code for stop in payload.stops),
            }
        )
    }
    origin = stations.get(payload.origin_code)
    destination = stations.get(payload.destination_code)
    if origin is None or destination is None:
        return (
            f"{payload.external_id}: unknown origin/destination "
            f"{payload.origin_code}/{payload.destination_code}"
        )
    missing_stops = [
        stop.station_code for stop in payload.stops if stop.station_code not in stations
    ]
    if missing_stops:
        codes = ", ".join(sorted(set(missing_stops)))
        return f"{payload.external_id}: unknown stop stations {codes}"

    with transaction.atomic():
        service, _created = upsert_train_service(
            external_id=payload.external_id,
            train_number=payload.train_number,
            origin=origin,
            destination=destination,
            service_date=payload.service_date,
            source=source,
        )
        for stop in payload.stops:
            upsert_scheduled_stop(
                train_service=service,
                station=stations[stop.station_code],
                stop_sequence=stop.stop_sequence,
                scheduled_arrival=stop.scheduled_arrival,
                scheduled_departure=stop.scheduled_departure,
                actual_arrival=stop.actual_arrival,
                actual_departure=stop.actual_departure,
            )
    return None


def synchronize_timetables(
    *,
    actor: User | None = None,
    provider: RailwayProvider,
    service_date: date | None = None,
) -> ExternalSyncRun:
    if actor is not None:
        actor = require_authenticated_user(actor)
        if not actor.has_perm(PERM_RUN_SYNC):
            raise PermissionDenied

    source = TrainService.Source(provider.name)
    run = ExternalSyncRun.objects.create(
        integration_name=provider.name,
        status=ExternalSyncRun.Status.RUNNING,
    )
    errors: list[str] = []
    created = 0
    updated = 0
    processed = 0
    try:
        services = provider.fetch_services(service_date=service_date)
        provider_errors = getattr(provider, "errors", [])
        if isinstance(provider_errors, list):
            errors.extend(str(item) for item in provider_errors)
        seen: set[tuple[str, date]] = set()
        for payload in services:
            key = (payload.external_id, payload.service_date)
            if key in seen:
                continue
            seen.add(key)
            processed += 1
            existed = TrainService.objects.filter(
                external_id=payload.external_id,
                service_date=payload.service_date,
            ).exists()
            persist_error = _persist_service(payload, source=source)
            if persist_error:
                errors.append(persist_error)
                continue
            if existed:
                updated += 1
            else:
                created += 1
        if errors and (created or updated):
            status = ExternalSyncRun.Status.PARTIAL
        elif errors:
            status = ExternalSyncRun.Status.FAILED
        else:
            status = ExternalSyncRun.Status.SUCCESS
        run.status = status
        run.records_processed = processed
        run.records_created = created
        run.records_updated = updated
        run.error_summary = _truncate_errors(errors)
        run.finished_at = timezone.now()
        run.save()
        logger.info(
            "Timetable sync provider=%s status=%s processed=%s created=%s updated=%s",
            provider.name,
            run.status,
            processed,
            created,
            updated,
        )
        return run
    except Exception as exc:
        run.status = ExternalSyncRun.Status.FAILED
        run.error_summary = _truncate_errors([str(exc), *errors])
        run.finished_at = timezone.now()
        run.records_processed = processed
        run.records_created = created
        run.records_updated = updated
        run.save()
        logger.exception("Timetable sync failed provider=%s", provider.name)
        return run
