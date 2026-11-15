"""CSV timetable import. Invalid rows are skipped and recorded on ``errors``."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from io import StringIO
from pathlib import Path

from pydantic import ValidationError

from apps.integrations.providers.schemas import ProviderService, ProviderStop

REQUIRED_COLUMNS = (
    "external_id",
    "train_number",
    "origin_code",
    "destination_code",
    "service_date",
    "stop_sequence",
    "station_code",
)


def _parse_datetime(raw: str) -> datetime | None:
    value = raw.strip()
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class CSVRailwayProvider:
    name = "csv"

    def __init__(self, *, content: str) -> None:
        self._content = content
        self.errors: list[str] = []

    @classmethod
    def from_path(cls, path: Path) -> CSVRailwayProvider:
        return cls(content=path.read_text(encoding="utf-8"))

    def fetch_services(self, *, service_date: date | None = None) -> list[ProviderService]:
        self.errors = []
        reader = csv.DictReader(StringIO(self._content))
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row.")
        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(missing)}")

        grouped: dict[tuple[str, str], dict[str, object]] = {}
        stops: dict[tuple[str, str], list[ProviderStop]] = defaultdict(list)
        for index, row in enumerate(reader, start=2):
            try:
                parsed_date = date.fromisoformat(row["service_date"].strip())
                stop = ProviderStop(
                    station_code=row["station_code"],
                    stop_sequence=int(row["stop_sequence"]),
                    scheduled_arrival=_parse_datetime(row.get("scheduled_arrival") or ""),
                    scheduled_departure=_parse_datetime(row.get("scheduled_departure") or ""),
                    actual_arrival=_parse_datetime(row.get("actual_arrival") or ""),
                    actual_departure=_parse_datetime(row.get("actual_departure") or ""),
                )
            except (TypeError, ValueError, ValidationError) as exc:
                self.errors.append(f"Row {index}: {exc}")
                continue
            if service_date is not None and parsed_date != service_date:
                continue
            key = (row["external_id"].strip(), parsed_date.isoformat())
            grouped[key] = {
                "external_id": row["external_id"],
                "train_number": row["train_number"],
                "origin_code": row["origin_code"],
                "destination_code": row["destination_code"],
                "service_date": parsed_date,
            }
            stops[key].append(stop)

        services: list[ProviderService] = []
        for key, header in grouped.items():
            service_day = header["service_date"]
            if not isinstance(service_day, date):
                self.errors.append(f"Service {key[0]}: invalid service date.")
                continue
            try:
                services.append(
                    ProviderService(
                        external_id=str(header["external_id"]),
                        train_number=str(header["train_number"]),
                        origin_code=str(header["origin_code"]),
                        destination_code=str(header["destination_code"]),
                        service_date=service_day,
                        stops=stops[key],
                    )
                )
            except ValidationError as exc:
                self.errors.append(f"Service {key[0]}: {exc}")
        return services
