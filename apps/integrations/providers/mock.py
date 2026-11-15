"""Deterministic in-process provider for local development and CI."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from apps.integrations.providers.schemas import ProviderService, ProviderStop


class MockRailwayProvider:
    name = "mock"

    def __init__(self, *, service_date: date | None = None) -> None:
        self._service_date = service_date

    def fetch_services(self, *, service_date: date | None = None) -> list[ProviderService]:
        operating_day = service_date or self._service_date or date(2026, 11, 15)
        departure = datetime(
            operating_day.year,
            operating_day.month,
            operating_day.day,
            7,
            0,
            tzinfo=UTC,
        )
        arrival = departure + timedelta(hours=1, minutes=30)
        late_departure = departure + timedelta(minutes=2)
        late_arrival = arrival + timedelta(minutes=10)
        return [
            ProviderService(
                external_id="MOCK-ICE501",
                train_number="ICE 501",
                origin_code="BHF",
                destination_code="HH",
                service_date=operating_day,
                stops=[
                    ProviderStop(
                        station_code="BHF",
                        stop_sequence=1,
                        scheduled_departure=departure,
                        actual_departure=late_departure,
                    ),
                    ProviderStop(
                        station_code="HH",
                        stop_sequence=2,
                        scheduled_arrival=arrival,
                        actual_arrival=late_arrival,
                    ),
                ],
            ),
            ProviderService(
                external_id="MOCK-RE42",
                train_number="RE 42",
                origin_code="HH",
                destination_code="BHF",
                service_date=operating_day,
                stops=[
                    ProviderStop(
                        station_code="HH",
                        stop_sequence=1,
                        scheduled_departure=departure + timedelta(hours=2),
                    ),
                    ProviderStop(
                        station_code="BHF",
                        stop_sequence=2,
                        scheduled_arrival=arrival + timedelta(hours=2),
                    ),
                ],
            ),
        ]
