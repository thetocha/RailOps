"""Allowed incident status transitions. Closed is terminal except admin reopen."""

from __future__ import annotations

from apps.incidents.models import Incident

Status = Incident.Status

ALLOWED_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.OPEN: frozenset({Status.IN_PROGRESS}),
    Status.IN_PROGRESS: frozenset({Status.RESOLVED, Status.OPEN}),
    Status.RESOLVED: frozenset({Status.CLOSED, Status.IN_PROGRESS}),
    Status.CLOSED: frozenset(),
}

CLOSED_REOPEN_TARGET = Status.IN_PROGRESS


def is_allowed_transition(
    *,
    current: Status,
    new: Status,
    can_reopen_closed: bool,
) -> bool:
    if current == new:
        return False
    if current == Status.CLOSED and new == CLOSED_REOPEN_TARGET:
        return can_reopen_closed
    return new in ALLOWED_TRANSITIONS[current]
