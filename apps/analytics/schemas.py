"""Typed analytics results. Views and reports must not receive raw DataFrames."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CountItem:
    key: str
    label: str
    count: int


@dataclass(frozen=True)
class StationDelay:
    station_code: str
    average_delay_seconds: float
    sample_count: int


@dataclass(frozen=True)
class DayDelay:
    day: date
    average_delay_seconds: float
    delayed_count: int
    measured_count: int


@dataclass(frozen=True)
class IncidentMetrics:
    total: int
    open_count: int
    resolved_count: int
    by_severity: tuple[CountItem, ...]
    by_category: tuple[CountItem, ...]
    average_resolution_seconds: float | None
    median_resolution_seconds: float | None
    volume_by_month: tuple[CountItem, ...]
    per_station: tuple[CountItem, ...]

    @classmethod
    def empty(cls) -> IncidentMetrics:
        return cls(
            total=0,
            open_count=0,
            resolved_count=0,
            by_severity=(),
            by_category=(),
            average_resolution_seconds=None,
            median_resolution_seconds=None,
            volume_by_month=(),
            per_station=(),
        )


@dataclass(frozen=True)
class DelayMetrics:
    total_services: int
    measured_services: int
    delayed_services: int
    average_delay_seconds: float | None
    median_delay_seconds: float | None
    maximum_delay_seconds: int | None
    on_time_percentage: float | None
    on_time_threshold_seconds: int
    by_station: tuple[StationDelay, ...]
    by_day: tuple[DayDelay, ...]

    @classmethod
    def empty(cls, *, on_time_threshold_seconds: int) -> DelayMetrics:
        return cls(
            total_services=0,
            measured_services=0,
            delayed_services=0,
            average_delay_seconds=None,
            median_delay_seconds=None,
            maximum_delay_seconds=None,
            on_time_percentage=None,
            on_time_threshold_seconds=on_time_threshold_seconds,
            by_station=(),
            by_day=(),
        )


@dataclass(frozen=True)
class OverviewMetrics:
    period_start: date
    period_end: date
    incidents: IncidentMetrics
    delays: DelayMetrics
