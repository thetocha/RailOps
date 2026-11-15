"""Incident write operations. Views must not duplicate this logic."""

from __future__ import annotations

import logging
from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.permissions import require_authenticated_user
from apps.incidents.models import Incident, IncidentEvent
from apps.incidents.permissions import (
    PERM_ADD_INCIDENT,
    PERM_CHANGE_INCIDENT,
    PERM_REOPEN_CLOSED,
)
from apps.incidents.transitions import is_allowed_transition
from apps.infrastructure.models import RailwayLine, Station

logger = logging.getLogger(__name__)


def _assert_perm(actor: User, perm: str) -> None:
    if not actor.has_perm(perm):
        raise PermissionDenied


def _record_event(
    *,
    incident: Incident,
    actor: User,
    event_type: IncidentEvent.EventType,
    description: str = "",
    previous_status: str | None = None,
    new_status: str | None = None,
) -> IncidentEvent:
    return IncidentEvent.objects.create(
        incident=incident,
        actor=actor,
        event_type=event_type,
        previous_status=previous_status,
        new_status=new_status,
        description=description,
    )


def _locked_incident(incident_id: UUID) -> Incident:
    try:
        return (
            Incident.objects.select_for_update()
            .select_related("station", "reporter")
            .get(pk=incident_id)
        )
    except Incident.DoesNotExist as exc:
        raise ValidationError("Incident not found.") from exc


@transaction.atomic
def create_incident(
    *,
    actor: User,
    title: str,
    description: str,
    station: Station,
    category: Incident.Category,
    severity: Incident.Severity,
    railway_line: RailwayLine | None = None,
) -> Incident:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_ADD_INCIDENT)
    cleaned_title = title.strip()
    cleaned_description = description.strip()
    if not cleaned_title:
        raise ValidationError({"title": "Title is required."})
    if not cleaned_description:
        raise ValidationError({"description": "Description is required."})
    if not station.is_active:
        raise ValidationError({"station": "Choose an active station."})
    if railway_line is not None and not railway_line.is_active:
        raise ValidationError({"railway_line": "Choose an active railway line."})
    incident = Incident.objects.create(
        title=cleaned_title,
        description=cleaned_description,
        station=station,
        railway_line=railway_line,
        category=category,
        severity=severity,
        status=Incident.Status.OPEN,
        reporter=actor,
    )
    _record_event(
        incident=incident,
        actor=actor,
        event_type=IncidentEvent.EventType.CREATED,
        new_status=Incident.Status.OPEN,
        description="Incident registered.",
    )
    logger.info("Created incident id=%s actor=%s", incident.pk, actor.username)
    return incident


@transaction.atomic
def update_incident(
    *,
    actor: User,
    incident_id: UUID,
    title: str,
    description: str,
    station: Station,
    category: Incident.Category,
    severity: Incident.Severity,
    railway_line: RailwayLine | None,
) -> Incident:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_CHANGE_INCIDENT)
    incident = _locked_incident(incident_id)
    cleaned_title = title.strip()
    cleaned_description = description.strip()
    if not cleaned_title:
        raise ValidationError({"title": "Title is required."})
    if not cleaned_description:
        raise ValidationError({"description": "Description is required."})
    if not station.is_active and station.pk != incident.station_id:
        raise ValidationError({"station": "Choose an active station."})
    if (
        railway_line is not None
        and not railway_line.is_active
        and railway_line.pk != incident.railway_line_id
    ):
        raise ValidationError({"railway_line": "Choose an active railway line."})

    previous_severity = incident.severity
    incident.title = cleaned_title
    incident.description = cleaned_description
    incident.station = station
    incident.railway_line = railway_line
    incident.category = category
    incident.severity = severity
    incident.save()
    if previous_severity != incident.severity:
        _record_event(
            incident=incident,
            actor=actor,
            event_type=IncidentEvent.EventType.SEVERITY_CHANGED,
            description=f"Severity changed from {previous_severity} to {incident.severity}.",
        )
    logger.info("Updated incident id=%s actor=%s", incident.pk, actor.username)
    return incident


@transaction.atomic
def assign_incident(
    *,
    actor: User,
    incident_id: UUID,
    assignee: User | None,
    comment: str | None = None,
) -> Incident:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_CHANGE_INCIDENT)
    incident = _locked_incident(incident_id)
    if assignee is not None and not assignee.is_active:
        raise ValidationError({"assigned_to": "Choose an active user."})
    incident.assigned_to = assignee
    incident.save(update_fields=["assigned_to", "updated_at"])
    if assignee is None:
        description = "Incident unassigned."
    else:
        description = f"Assigned to {assignee.username}."
    if comment and comment.strip():
        description = f"{description} {comment.strip()}"
    _record_event(
        incident=incident,
        actor=actor,
        event_type=IncidentEvent.EventType.ASSIGNED,
        description=description,
    )
    logger.info("Assigned incident id=%s actor=%s", incident.pk, actor.username)
    return incident


@transaction.atomic
def change_incident_severity(
    *,
    actor: User,
    incident_id: UUID,
    severity: Incident.Severity,
    comment: str | None = None,
) -> Incident:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_CHANGE_INCIDENT)
    incident = _locked_incident(incident_id)
    if incident.severity == severity:
        return incident
    previous = incident.severity
    incident.severity = severity
    incident.save(update_fields=["severity", "updated_at"])
    description = f"Severity changed from {previous} to {severity}."
    if comment and comment.strip():
        description = f"{description} {comment.strip()}"
    _record_event(
        incident=incident,
        actor=actor,
        event_type=IncidentEvent.EventType.SEVERITY_CHANGED,
        description=description,
    )
    logger.info("Changed incident severity id=%s actor=%s", incident.pk, actor.username)
    return incident


@transaction.atomic
def transition_incident(
    *,
    incident_id: UUID,
    new_status: Incident.Status,
    actor: User,
    comment: str | None = None,
) -> Incident:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_CHANGE_INCIDENT)
    incident = _locked_incident(incident_id)
    current = Incident.Status(incident.status)
    if not is_allowed_transition(
        current=current,
        new=new_status,
        can_reopen_closed=actor.has_perm(PERM_REOPEN_CLOSED),
    ):
        raise ValidationError(f"Cannot change status from {current.label} to {new_status.label}.")

    previous_status = incident.status
    incident.status = new_status
    if new_status == Incident.Status.RESOLVED:
        incident.resolved_at = timezone.now()
        event_type = IncidentEvent.EventType.RESOLVED
    elif new_status in {Incident.Status.OPEN, Incident.Status.IN_PROGRESS}:
        incident.resolved_at = None
        event_type = IncidentEvent.EventType.STATUS_CHANGED
    else:
        event_type = IncidentEvent.EventType.STATUS_CHANGED
    incident.save(update_fields=["status", "resolved_at", "updated_at"])

    description = f"Status changed from {previous_status} to {new_status}."
    if comment and comment.strip():
        description = f"{description} {comment.strip()}"
    _record_event(
        incident=incident,
        actor=actor,
        event_type=event_type,
        previous_status=previous_status,
        new_status=new_status,
        description=description,
    )
    logger.info(
        "Transitioned incident id=%s from=%s to=%s actor=%s",
        incident.pk,
        previous_status,
        new_status,
        actor.username,
    )
    return incident
