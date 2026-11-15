"""Read queries for incidents."""

from __future__ import annotations

from uuid import UUID

from django.db.models import Q, QuerySet

from apps.incidents.models import Incident, IncidentEvent
from apps.incidents.transitions import (
    ALLOWED_TRANSITIONS,
    CLOSED_REOPEN_TARGET,
    is_allowed_transition,
)


def incident_directory(
    *,
    search: str = "",
    status: str | None = None,
    severity: str | None = None,
    category: str | None = None,
    station_id: UUID | None = None,
) -> QuerySet[Incident]:
    queryset = Incident.objects.select_related(
        "station",
        "railway_line",
        "reporter",
        "assigned_to",
    )
    if status:
        queryset = queryset.filter(status=status)
    if severity:
        queryset = queryset.filter(severity=severity)
    if category:
        queryset = queryset.filter(category=category)
    if station_id is not None:
        queryset = queryset.filter(station_id=station_id)
    term = search.strip()
    if term:
        queryset = queryset.filter(
            Q(title__icontains=term)
            | Q(description__icontains=term)
            | Q(station__name__icontains=term)
            | Q(station__code__icontains=term)
        )
    return queryset.order_by("-reported_at", "title")


def incident_with_history(incident_id: UUID) -> Incident:
    return (
        Incident.objects.select_related(
            "station",
            "railway_line",
            "reporter",
            "assigned_to",
        )
        .prefetch_related("events__actor")
        .get(pk=incident_id)
    )


def events_for_incident(incident: Incident) -> QuerySet[IncidentEvent]:
    return incident.events.select_related("actor").order_by("created_at", "id")


def allowed_next_statuses(
    *,
    current: Incident.Status,
    can_reopen_closed: bool,
) -> list[Incident.Status]:
    targets = set(ALLOWED_TRANSITIONS[current])
    if can_reopen_closed and is_allowed_transition(
        current=current,
        new=CLOSED_REOPEN_TARGET,
        can_reopen_closed=True,
    ):
        targets.add(CLOSED_REOPEN_TARGET)
    return sorted(targets, key=lambda status: status.label)
