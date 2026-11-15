"""Pandas transformations over bounded record lists. No ORM access here."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

import pandas as pd

from apps.analytics.schemas import (
    CountItem,
    DayDelay,
    DelayMetrics,
    IncidentMetrics,
    StationDelay,
)
from apps.incidents.models import Incident
from apps.timetables.models import ON_TIME_THRESHOLD_SECONDS, Delay

OPEN_STATUSES = frozenset({Incident.Status.OPEN, Incident.Status.IN_PROGRESS})
RESOLVED_STATUSES = frozenset({Incident.Status.RESOLVED, Incident.Status.CLOSED})

_SEVERITY_LABELS: dict[str, str] = dict(Incident.Severity.choices)
_CATEGORY_LABELS: dict[str, str] = dict(Incident.Category.choices)
_KIND_RANK = {Delay.Kind.ARRIVAL: 0, Delay.Kind.DEPARTURE: 1}


def calculate_incident_metrics(records: list[dict[str, object]]) -> IncidentMetrics:
    if not records:
        return IncidentMetrics.empty()
    frame = pd.DataFrame.from_records(records)
    total = int(len(frame))
    status = frame["status"].astype(str)
    open_count = int(status.isin(OPEN_STATUSES).sum())
    resolved_count = int(status.isin(RESOLVED_STATUSES).sum())
    resolution = _resolution_seconds(frame)
    average = float(resolution.mean()) if not resolution.empty else None
    median = float(resolution.median()) if not resolution.empty else None
    return IncidentMetrics(
        total=total,
        open_count=open_count,
        resolved_count=resolved_count,
        by_severity=_counts(frame["severity"], _SEVERITY_LABELS),
        by_category=_counts(frame["category"], _CATEGORY_LABELS),
        average_resolution_seconds=average,
        median_resolution_seconds=median,
        volume_by_month=_volume_by_month(frame),
        per_station=_counts(frame["station_code"], labels=None),
    )


def calculate_delay_metrics(
    records: list[dict[str, object]],
    *,
    total_services: int,
    on_time_threshold_seconds: int = ON_TIME_THRESHOLD_SECONDS,
) -> DelayMetrics:
    if total_services < 0:
        raise ValueError("total_services must be >= 0")
    if total_services == 0 or not records:
        empty = DelayMetrics.empty(on_time_threshold_seconds=on_time_threshold_seconds)
        if total_services == 0:
            return empty
        return DelayMetrics(
            total_services=total_services,
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
    frame = pd.DataFrame.from_records(records)
    frame["kind_rank"] = frame["kind"].map(_KIND_RANK).fillna(99)
    chosen = frame.sort_values(["service_id", "kind_rank"]).drop_duplicates(
        "service_id",
        keep="first",
    )
    delays = pd.to_numeric(chosen["delay_seconds"], errors="coerce").dropna()
    if delays.empty:
        return DelayMetrics(
            total_services=total_services,
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
    measured = int(len(delays))
    delayed = int((delays > on_time_threshold_seconds).sum())
    on_time = int((delays <= on_time_threshold_seconds).sum())
    chosen = chosen.loc[delays.index]
    return DelayMetrics(
        total_services=total_services,
        measured_services=measured,
        delayed_services=delayed,
        average_delay_seconds=float(delays.mean()),
        median_delay_seconds=float(delays.median()),
        maximum_delay_seconds=int(delays.max()),
        on_time_percentage=(on_time / measured) * 100.0,
        on_time_threshold_seconds=on_time_threshold_seconds,
        by_station=_delay_by_station(chosen, delays),
        by_day=_delay_by_day(chosen, delays, on_time_threshold_seconds),
    )


def _counts(
    series: pd.Series[Any],
    labels: Mapping[str, str] | None,
) -> tuple[CountItem, ...]:
    value_counts = series.astype(str).value_counts()
    if labels is None:
        items = [
            CountItem(key=str(key), label=str(key), count=int(count))
            for key, count in value_counts.sort_values(ascending=False).items()
        ]
        return tuple(items)
    items = [
        CountItem(key=key, label=label, count=int(value_counts.get(key, 0)))
        for key, label in labels.items()
    ]
    return tuple(items)


def _resolution_seconds(frame: pd.DataFrame) -> pd.Series[Any]:
    if "resolved_at" not in frame.columns or "reported_at" not in frame.columns:
        return pd.Series(dtype="float64")
    reported = pd.to_datetime(frame["reported_at"], utc=True, errors="coerce", format="mixed")
    resolved = pd.to_datetime(frame["resolved_at"], utc=True, errors="coerce", format="mixed")
    delta = (resolved - reported).dt.total_seconds()
    return delta[delta.notna() & (delta >= 0)]


def _volume_by_month(frame: pd.DataFrame) -> tuple[CountItem, ...]:
    reported = pd.to_datetime(
        frame["reported_at"], utc=True, errors="coerce", format="mixed"
    ).dropna()
    if reported.empty:
        return ()
    months = reported.dt.strftime("%Y-%m")
    counts = months.value_counts().sort_index()
    return tuple(
        CountItem(key=str(key), label=str(key), count=int(count)) for key, count in counts.items()
    )


def _delay_by_station(chosen: pd.DataFrame, delays: pd.Series[Any]) -> tuple[StationDelay, ...]:
    working = chosen.loc[delays.index, ["station_code"]].copy()
    working["delay_seconds"] = delays
    grouped = working.groupby("station_code", dropna=True)["delay_seconds"]
    items = [
        StationDelay(
            station_code=str(station),
            average_delay_seconds=float(values.mean()),
            sample_count=int(values.count()),
        )
        for station, values in grouped
    ]
    items.sort(key=lambda item: (-item.average_delay_seconds, item.station_code))
    return tuple(items)


def _delay_by_day(
    chosen: pd.DataFrame,
    delays: pd.Series[Any],
    on_time_threshold_seconds: int,
) -> tuple[DayDelay, ...]:
    working = chosen.loc[delays.index, ["service_date"]].copy()
    working["delay_seconds"] = delays
    working["service_date"] = pd.to_datetime(working["service_date"], errors="coerce").dt.date
    working = working.dropna(subset=["service_date"])
    if working.empty:
        return ()
    items: list[DayDelay] = []
    grouped = working.groupby("service_date", sort=True)["delay_seconds"]
    for day, values in grouped:
        items.append(
            DayDelay(
                day=_as_date(day),
                average_delay_seconds=float(values.mean()),
                delayed_count=int((values > on_time_threshold_seconds).sum()),
                measured_count=int(values.count()),
            )
        )
    return tuple(items)


def _as_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError(f"Invalid service date: {value!r}")
