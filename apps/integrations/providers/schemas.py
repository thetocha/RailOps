"""Validated provider payloads. Untrusted data must pass these schemas first."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class ProviderStop(BaseModel):
    station_code: str = Field(min_length=1, max_length=32)
    stop_sequence: int = Field(ge=1)
    scheduled_arrival: datetime | None = None
    scheduled_departure: datetime | None = None
    actual_arrival: datetime | None = None
    actual_departure: datetime | None = None

    @field_validator("station_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("Station code is required.")
        return cleaned

    @field_validator(
        "scheduled_arrival",
        "scheduled_departure",
        "actual_arrival",
        "actual_departure",
    )
    @classmethod
    def require_aware_datetimes(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware.")
        return value


class ProviderService(BaseModel):
    external_id: str = Field(min_length=1, max_length=64)
    train_number: str = Field(min_length=1, max_length=32)
    origin_code: str = Field(min_length=1, max_length=32)
    destination_code: str = Field(min_length=1, max_length=32)
    service_date: date
    stops: list[ProviderStop] = Field(min_length=1)

    @field_validator("external_id", "train_number")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value is required.")
        return cleaned

    @field_validator("origin_code", "destination_code")
    @classmethod
    def uppercase_codes(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("Station code is required.")
        return cleaned
