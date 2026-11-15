from __future__ import annotations

from datetime import datetime
from io import StringIO
from pathlib import Path

import httpx
import pytest
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.test import Client, override_settings
from pydantic import ValidationError

from apps.accounts.models import User
from apps.infrastructure.models import Station
from apps.integrations.models import ExternalSyncRun
from apps.integrations.providers.csv import CSVRailwayProvider
from apps.integrations.providers.httpx_client import ExternalRailwayAPIClient
from apps.integrations.providers.mock import MockRailwayProvider
from apps.integrations.providers.schemas import ProviderStop
from apps.integrations.services import build_provider, synchronize_timetables
from apps.timetables.models import Delay, TrainService

pytestmark = pytest.mark.django_db

SAMPLE_CSV = Path("apps/integrations/fixtures/sample_timetable.csv")


def test_mock_sync_is_idempotent(
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    first = synchronize_timetables(actor=administrator, provider=MockRailwayProvider())
    assert first.status == ExternalSyncRun.Status.SUCCESS
    assert first.records_created == 2
    second = synchronize_timetables(actor=administrator, provider=MockRailwayProvider())
    assert second.status == ExternalSyncRun.Status.SUCCESS
    assert second.records_created == 0
    assert second.records_updated == 2
    assert TrainService.objects.count() == 2
    ice = TrainService.objects.get(external_id="MOCK-ICE501")
    arrival = Delay.objects.get(train_service=ice, kind=Delay.Kind.ARRIVAL)
    departure = Delay.objects.get(train_service=ice, kind=Delay.Kind.DEPARTURE)
    assert arrival.delay_seconds == 600
    assert departure.delay_seconds == 120


def test_csv_import_persists_validated_rows(
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    provider = CSVRailwayProvider.from_path(SAMPLE_CSV)
    run = synchronize_timetables(actor=administrator, provider=provider)
    assert run.status == ExternalSyncRun.Status.SUCCESS
    service = TrainService.objects.get(external_id="CSV-ICE9")
    assert service.train_number == "ICE 9"
    assert service.stops.count() == 2


def test_invalid_csv_row_is_reported_without_creating_service(
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    content = (
        "external_id,train_number,origin_code,destination_code,service_date,"
        "stop_sequence,station_code,scheduled_arrival,scheduled_departure,"
        "actual_arrival,actual_departure\n"
        "BAD,ICE X,BHF,HH,not-a-date,1,BHF,,,,\n"
    )
    provider = CSVRailwayProvider(content=content)
    run = synchronize_timetables(actor=administrator, provider=provider)
    assert run.status == ExternalSyncRun.Status.FAILED
    assert "Row 2" in run.error_summary
    assert not TrainService.objects.exists()


def test_missing_station_does_not_corrupt_existing_services(
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    synchronize_timetables(actor=administrator, provider=MockRailwayProvider())
    content = (
        "external_id,train_number,origin_code,destination_code,service_date,"
        "stop_sequence,station_code,scheduled_arrival,scheduled_departure,"
        "actual_arrival,actual_departure\n"
        "CSV-UNKNOWN,ICE X,XXX,YYY,2026-11-15,1,XXX,,,,\n"
    )
    provider = CSVRailwayProvider(content=content)
    run = synchronize_timetables(actor=administrator, provider=provider)
    assert run.status == ExternalSyncRun.Status.FAILED
    assert "unknown origin/destination" in run.error_summary
    assert TrainService.objects.filter(external_id="MOCK-ICE501").exists()
    assert not TrainService.objects.filter(external_id="CSV-UNKNOWN").exists()


def test_http_client_uses_mock_transport(
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    payload = [
        service.model_dump(mode="json") for service in MockRailwayProvider().fetch_services()
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/services")
        return httpx.Response(200, json=payload)

    client = ExternalRailwayAPIClient(
        base_url="https://timetable.example.test",
        api_key="not-a-real-key",
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )
    run = synchronize_timetables(actor=administrator, provider=client)
    assert run.status == ExternalSyncRun.Status.SUCCESS
    assert TrainService.objects.filter(source=TrainService.Source.HTTP).count() == 2


def test_http_client_does_not_retry_unauthorized() -> None:
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(401, json={"detail": "no"})

    client = ExternalRailwayAPIClient(
        base_url="https://timetable.example.test",
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )
    with pytest.raises(httpx.HTTPStatusError):
        client.fetch_services()
    assert calls["count"] == 1


def test_http_client_retries_transient_status() -> None:
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 2:
            return httpx.Response(503, headers={"Retry-After": "0"})
        return httpx.Response(200, json=[])

    client = ExternalRailwayAPIClient(
        base_url="https://timetable.example.test",
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )
    assert client.fetch_services() == []
    assert calls["count"] == 2


def test_viewer_cannot_run_sync(
    viewer: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    with pytest.raises(PermissionDenied):
        synchronize_timetables(actor=viewer, provider=MockRailwayProvider())


def test_viewer_can_list_services_but_not_sync_runs(
    client: Client,
    viewer: User,
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    synchronize_timetables(actor=administrator, provider=MockRailwayProvider())
    client.force_login(viewer)
    listing = client.get("/services/")
    assert listing.status_code == 200
    assert b"ICE 501" in listing.content
    assert client.get("/integrations/sync-runs/").status_code == 403
    assert client.post("/integrations/sync-runs/run/", {"provider": "mock"}).status_code == 403


def test_administrator_can_run_mock_sync_from_html(
    client: Client,
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    client.force_login(administrator)
    response = client.post("/integrations/sync-runs/run/", {"provider": "mock"})
    assert response.status_code == 302
    assert ExternalSyncRun.objects.filter(status=ExternalSyncRun.Status.SUCCESS).exists()


def test_sync_requires_csrf(
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(administrator)
    response = client.post("/integrations/sync-runs/run/", {"provider": "mock"})
    assert response.status_code == 403
    assert not TrainService.objects.exists()


def test_dispatcher_can_view_services_but_not_run_sync(
    client: Client,
    dispatcher: User,
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    synchronize_timetables(actor=administrator, provider=MockRailwayProvider())
    client.force_login(dispatcher)
    listing = client.get("/services/")
    assert listing.status_code == 200
    assert b"ICE 501" in listing.content
    assert client.get("/integrations/sync-runs/").status_code == 403
    assert client.post("/integrations/sync-runs/run/", {"provider": "mock"}).status_code == 403


def test_service_list_filters_by_date(
    client: Client,
    viewer: User,
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    synchronize_timetables(actor=administrator, provider=MockRailwayProvider())
    client.force_login(viewer)
    matching = client.get("/services/", {"date": "2026-11-15"})
    assert matching.status_code == 200
    assert b"ICE 501" in matching.content
    empty = client.get("/services/", {"date": "2020-01-01"})
    assert empty.status_code == 200
    assert b"ICE 501" not in empty.content


def test_sync_timetables_command(
    berlin_hamburg: tuple[Station, Station],
) -> None:
    stdout = StringIO()
    call_command("sync_timetables", "--provider", "mock", stdout=stdout)
    assert TrainService.objects.count() == 2
    assert "success" in stdout.getvalue()


def test_http_client_does_not_retry_bad_request() -> None:
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(400, json={"detail": "bad"})

    client = ExternalRailwayAPIClient(
        base_url="https://timetable.example.test",
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )
    with pytest.raises(httpx.HTTPStatusError):
        client.fetch_services()
    assert calls["count"] == 1


def test_http_failure_does_not_corrupt_existing_services(
    administrator: User,
    berlin_hamburg: tuple[Station, Station],
) -> None:
    synchronize_timetables(actor=administrator, provider=MockRailwayProvider())

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "down"})

    client = ExternalRailwayAPIClient(
        base_url="https://timetable.example.test",
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )
    run = synchronize_timetables(actor=administrator, provider=client)
    assert run.status == ExternalSyncRun.Status.FAILED
    assert TrainService.objects.filter(external_id="MOCK-ICE501").exists()
    assert TrainService.objects.filter(source=TrainService.Source.HTTP).count() == 0


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProviderStop(
            station_code="BHF",
            stop_sequence=1,
            scheduled_arrival=datetime(2026, 11, 15, 8, 0),
        )


def test_build_provider_http_requires_url() -> None:
    with (
        override_settings(EXTERNAL_RAILWAY_API_URL=""),
        pytest.raises(ValueError, match="not configured"),
    ):
        build_provider(name="http")
