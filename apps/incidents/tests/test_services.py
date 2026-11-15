from __future__ import annotations

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.incidents.models import Incident, IncidentEvent
from apps.incidents.services import (
    assign_incident,
    change_incident_severity,
    create_incident,
    transition_incident,
    update_incident,
)
from apps.infrastructure.models import RailwayLine, Station

pytestmark = pytest.mark.django_db


def _advance_to(
    incident: Incident,
    actor: User,
    *statuses: Incident.Status,
) -> Incident:
    current = incident
    for status in statuses:
        current = transition_incident(
            incident_id=current.pk,
            new_status=status,
            actor=actor,
        )
    return current


def test_create_incident_records_history(dispatcher: User, berlin: Station) -> None:
    incident = create_incident(
        actor=dispatcher,
        title="  Track obstruction ",
        description=" Tree on the line. ",
        station=berlin,
        category=Incident.Category.TRACK_OBSTRUCTION,
        severity=Incident.Severity.MEDIUM,
    )
    assert incident.title == "Track obstruction"
    assert incident.status == Incident.Status.OPEN
    event = incident.events.get()
    assert event.event_type == IncidentEvent.EventType.CREATED
    assert event.actor_id == dispatcher.pk
    assert event.new_status == Incident.Status.OPEN


def test_viewer_cannot_create_or_transition(
    viewer: User,
    berlin: Station,
    open_incident: Incident,
) -> None:
    with pytest.raises(PermissionDenied):
        create_incident(
            actor=viewer,
            title="Forbidden",
            description="No",
            station=berlin,
            category=Incident.Category.OTHER,
            severity=Incident.Severity.LOW,
        )
    with pytest.raises(PermissionDenied):
        transition_incident(
            incident_id=open_incident.pk,
            new_status=Incident.Status.IN_PROGRESS,
            actor=viewer,
        )
    open_incident.refresh_from_db()
    assert open_incident.status == Incident.Status.OPEN


def test_happy_path_lifecycle_sets_and_clears_resolved_at(
    dispatcher: User,
    open_incident: Incident,
) -> None:
    in_progress = transition_incident(
        incident_id=open_incident.pk,
        new_status=Incident.Status.IN_PROGRESS,
        actor=dispatcher,
        comment="Crew dispatched.",
    )
    assert in_progress.status == Incident.Status.IN_PROGRESS
    assert in_progress.resolved_at is None

    resolved = transition_incident(
        incident_id=open_incident.pk,
        new_status=Incident.Status.RESOLVED,
        actor=dispatcher,
    )
    assert resolved.status == Incident.Status.RESOLVED
    assert resolved.resolved_at is not None
    assert resolved.events.filter(event_type=IncidentEvent.EventType.RESOLVED).exists()

    reopened = transition_incident(
        incident_id=open_incident.pk,
        new_status=Incident.Status.IN_PROGRESS,
        actor=dispatcher,
    )
    assert reopened.status == Incident.Status.IN_PROGRESS
    assert reopened.resolved_at is None

    closed = _advance_to(
        reopened,
        dispatcher,
        Incident.Status.RESOLVED,
        Incident.Status.CLOSED,
    )
    assert closed.status == Incident.Status.CLOSED
    assert closed.resolved_at is not None


def test_invalid_transition_is_rejected(dispatcher: User, open_incident: Incident) -> None:
    with pytest.raises(ValidationError):
        transition_incident(
            incident_id=open_incident.pk,
            new_status=Incident.Status.CLOSED,
            actor=dispatcher,
        )
    open_incident.refresh_from_db()
    assert open_incident.status == Incident.Status.OPEN
    assert open_incident.events.count() == 1


def test_dispatcher_cannot_reopen_closed_incident(
    dispatcher: User,
    open_incident: Incident,
) -> None:
    closed = _advance_to(
        open_incident,
        dispatcher,
        Incident.Status.IN_PROGRESS,
        Incident.Status.RESOLVED,
        Incident.Status.CLOSED,
    )
    with pytest.raises(ValidationError):
        transition_incident(
            incident_id=closed.pk,
            new_status=Incident.Status.IN_PROGRESS,
            actor=dispatcher,
        )
    closed.refresh_from_db()
    assert closed.status == Incident.Status.CLOSED


def test_administrator_can_reopen_closed_incident(
    administrator: User,
    dispatcher: User,
    open_incident: Incident,
) -> None:
    closed = _advance_to(
        open_incident,
        dispatcher,
        Incident.Status.IN_PROGRESS,
        Incident.Status.RESOLVED,
        Incident.Status.CLOSED,
    )
    reopened = transition_incident(
        incident_id=closed.pk,
        new_status=Incident.Status.IN_PROGRESS,
        actor=administrator,
        comment="Reopened after inspection.",
    )
    assert reopened.status == Incident.Status.IN_PROGRESS
    assert reopened.resolved_at is None


def test_assign_and_severity_create_events(
    dispatcher: User,
    administrator: User,
    open_incident: Incident,
) -> None:
    assigned = assign_incident(
        actor=dispatcher,
        incident_id=open_incident.pk,
        assignee=administrator,
        comment="Please take this.",
    )
    assert assigned.assigned_to_id == administrator.pk
    changed = change_incident_severity(
        actor=dispatcher,
        incident_id=open_incident.pk,
        severity=Incident.Severity.CRITICAL,
    )
    assert changed.severity == Incident.Severity.CRITICAL
    types = list(open_incident.events.order_by("created_at").values_list("event_type", flat=True))
    assert IncidentEvent.EventType.ASSIGNED in types
    assert IncidentEvent.EventType.SEVERITY_CHANGED in types


def test_update_incident_records_severity_change(
    dispatcher: User,
    open_incident: Incident,
    berlin: Station,
    berlin_hamburg: RailwayLine,
) -> None:
    updated = update_incident(
        actor=dispatcher,
        incident_id=open_incident.pk,
        title=open_incident.title,
        description=open_incident.description,
        station=berlin,
        railway_line=berlin_hamburg,
        category=Incident.Category.SIGNAL_FAILURE,
        severity=Incident.Severity.LOW,
    )
    assert updated.railway_line_id == berlin_hamburg.pk
    assert updated.severity == Incident.Severity.LOW
    assert updated.events.filter(event_type=IncidentEvent.EventType.SEVERITY_CHANGED).exists()


def test_missing_incident_raises_validation_error(dispatcher: User) -> None:
    from uuid import uuid4

    with pytest.raises(ValidationError):
        transition_incident(
            incident_id=uuid4(),
            new_status=Incident.Status.IN_PROGRESS,
            actor=dispatcher,
        )
