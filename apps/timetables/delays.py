"""Pure delay calculations. Missing actuals are not treated as zero."""

from __future__ import annotations

from datetime import datetime

from apps.timetables.models import Delay, ScheduledStop


def delay_seconds(*, scheduled: datetime, actual: datetime) -> int:
    """Signed delay in seconds. Negative means early."""
    return int((actual - scheduled).total_seconds())


def format_delay_seconds(seconds: int) -> str:
    """User-facing delay label. Internal storage remains seconds."""
    sign = "-" if seconds < 0 else ""
    magnitude = abs(seconds)
    minutes, remainder = divmod(magnitude, 60)
    if minutes and remainder:
        return f"{sign}{minutes} min {remainder} s"
    if minutes:
        return f"{sign}{minutes} min"
    return f"{sign}{magnitude} s"


def measured_event(
    stop: ScheduledStop,
) -> tuple[Delay.Kind, datetime, datetime] | None:
    """MVP: arrival when both arrival times exist, otherwise the one pair that exists."""
    if stop.scheduled_arrival is not None and stop.actual_arrival is not None:
        return Delay.Kind.ARRIVAL, stop.scheduled_arrival, stop.actual_arrival
    if stop.scheduled_departure is not None and stop.actual_departure is not None:
        return Delay.Kind.DEPARTURE, stop.scheduled_departure, stop.actual_departure
    return None
