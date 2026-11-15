from __future__ import annotations

from django import template

from apps.timetables.delays import format_delay_seconds

register = template.Library()


@register.filter(name="format_delay")
def format_delay(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    return format_delay_seconds(seconds)
