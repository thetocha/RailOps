"""Read queries for stations and railway lines."""

from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.infrastructure.models import RailwayLine, Station

ActiveFilter = bool | None


def parse_active_filter(raw: str | None) -> ActiveFilter:
    """Return True (active), False (inactive), or None (all). Invalid values are active."""
    if raw in (None, "", "active"):
        return True
    if raw == "inactive":
        return False
    if raw == "all":
        return None
    return True


def station_directory(
    *,
    search: str = "",
    is_active: ActiveFilter = True,
) -> QuerySet[Station]:
    queryset = Station.objects.all()
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    term = search.strip()
    if term:
        queryset = queryset.filter(
            Q(name__icontains=term) | Q(code__icontains=term) | Q(city__icontains=term)
        )
    return queryset.order_by("name", "code")


def railway_line_directory(
    *,
    search: str = "",
    is_active: ActiveFilter = True,
) -> QuerySet[RailwayLine]:
    queryset = RailwayLine.objects.select_related("start_station", "end_station")
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    term = search.strip()
    if term:
        queryset = queryset.filter(
            Q(name__icontains=term)
            | Q(code__icontains=term)
            | Q(start_station__name__icontains=term)
            | Q(end_station__name__icontains=term)
            | Q(start_station__code__icontains=term)
            | Q(end_station__code__icontains=term)
        )
    return queryset.order_by("name", "code")


def lines_for_station(station: Station) -> QuerySet[RailwayLine]:
    return (
        RailwayLine.objects.filter(Q(start_station=station) | Q(end_station=station))
        .select_related("start_station", "end_station")
        .order_by("name")
    )
