"""Incident permission helpers. Views must not branch on role group names."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER

PERM_VIEW_INCIDENT = "incidents.view_incident"
PERM_ADD_INCIDENT = "incidents.add_incident"
PERM_CHANGE_INCIDENT = "incidents.change_incident"
PERM_REOPEN_CLOSED = "incidents.reopen_closed_incident"

_INCIDENT_MANAGED = frozenset(
    {
        "view_incident",
        "add_incident",
        "change_incident",
        "delete_incident",
        "reopen_closed_incident",
    }
)
_EVENT_MANAGED = frozenset(
    {
        "view_incidentevent",
        "add_incidentevent",
        "change_incidentevent",
        "delete_incidentevent",
    }
)

_ADMIN_INCIDENT = frozenset(
    {
        "view_incident",
        "add_incident",
        "change_incident",
        "reopen_closed_incident",
    }
)
_DISPATCHER_INCIDENT = frozenset({"view_incident", "add_incident", "change_incident"})
_VIEWER_INCIDENT = frozenset({"view_incident"})
_READ_EVENT = frozenset({"view_incidentevent"})

PERMISSION_CODENAMES_BY_GROUP: dict[str, dict[str, frozenset[str]]] = {
    GROUP_ADMINISTRATOR: {"incident": _ADMIN_INCIDENT, "incidentevent": _READ_EVENT},
    GROUP_DISPATCHER: {"incident": _DISPATCHER_INCIDENT, "incidentevent": _READ_EVENT},
    GROUP_VIEWER: {"incident": _VIEWER_INCIDENT, "incidentevent": _READ_EVENT},
}

_MANAGED_BY_MODEL: dict[str, frozenset[str]] = {
    "incident": _INCIDENT_MANAGED,
    "incidentevent": _EVENT_MANAGED,
}


def can_view_incidents(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_VIEW_INCIDENT)
    )


def can_manage_incidents(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_ADD_INCIDENT)
        and user.has_perm(PERM_CHANGE_INCIDENT)
    )


def can_reopen_closed_incident(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_REOPEN_CLOSED)
    )


@transaction.atomic
def ensure_incident_permissions() -> None:
    """Sync incident permissions onto the three role groups. Idempotent."""
    for model in ("incident", "incidentevent"):
        try:
            content_type = ContentType.objects.get(app_label="incidents", model=model)
        except ContentType.DoesNotExist as exc:
            raise RuntimeError(
                f"ContentType for incidents.{model} is missing. Run migrations first."
            ) from exc
        managed = _MANAGED_BY_MODEL[model]
        permissions = list(
            Permission.objects.filter(content_type=content_type, codename__in=managed)
        )
        by_codename = {permission.codename: permission for permission in permissions}
        for group_name, expected_by_model in PERMISSION_CODENAMES_BY_GROUP.items():
            expected = expected_by_model[model]
            missing = sorted(expected - by_codename.keys())
            if missing:
                missing_display = ", ".join(f"incidents.{codename}" for codename in missing)
                raise RuntimeError(
                    "Missing permission(s) "
                    f"{missing_display}. Run migrations so Django can create them."
                )
            group, _created = Group.objects.get_or_create(name=group_name)
            group.permissions.add(*(by_codename[codename] for codename in expected))
            stale = group.permissions.filter(
                content_type=content_type,
                codename__in=managed - expected,
            )
            if stale.exists():
                group.permissions.remove(*stale)


class ViewIncidentRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW_INCIDENT
    raise_exception = True


class AddIncidentRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_ADD_INCIDENT
    raise_exception = True


class ChangeIncidentRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_CHANGE_INCIDENT
    raise_exception = True
