"""Station and railway-line permission helpers.

Authorization must use ``user.has_perm(...)`` or these mixins. Do not branch
on role group names in views.

``ensure_infrastructure_permissions`` attaches model permissions to the three
role groups. It only adds or removes permissions whose content type is
``infrastructure.station`` or ``infrastructure.railwayline``.
"""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER

PERM_VIEW_STATION = "infrastructure.view_station"
PERM_ADD_STATION = "infrastructure.add_station"
PERM_CHANGE_STATION = "infrastructure.change_station"
PERM_VIEW_RAILWAY_LINE = "infrastructure.view_railwayline"
PERM_ADD_RAILWAY_LINE = "infrastructure.add_railwayline"
PERM_CHANGE_RAILWAY_LINE = "infrastructure.change_railwayline"

_STATION_MANAGED = frozenset({"view_station", "add_station", "change_station", "delete_station"})
_LINE_MANAGED = frozenset(
    {"view_railwayline", "add_railwayline", "change_railwayline", "delete_railwayline"}
)

_ADMIN_STATION = frozenset({"view_station", "add_station", "change_station"})
_ADMIN_LINE = frozenset({"view_railwayline", "add_railwayline", "change_railwayline"})
_READ_STATION = frozenset({"view_station"})
_READ_LINE = frozenset({"view_railwayline"})

PERMISSION_CODENAMES_BY_GROUP: dict[str, dict[str, frozenset[str]]] = {
    GROUP_ADMINISTRATOR: {"station": _ADMIN_STATION, "railwayline": _ADMIN_LINE},
    GROUP_DISPATCHER: {"station": _READ_STATION, "railwayline": _READ_LINE},
    GROUP_VIEWER: {"station": _READ_STATION, "railwayline": _READ_LINE},
}

_MANAGED_BY_MODEL: dict[str, frozenset[str]] = {
    "station": _STATION_MANAGED,
    "railwayline": _LINE_MANAGED,
}


def can_view_stations(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_VIEW_STATION)
    )


def can_manage_stations(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_ADD_STATION)
        and user.has_perm(PERM_CHANGE_STATION)
    )


def can_view_railway_lines(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_VIEW_RAILWAY_LINE)
    )


def can_manage_railway_lines(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_ADD_RAILWAY_LINE)
        and user.has_perm(PERM_CHANGE_RAILWAY_LINE)
    )


@transaction.atomic
def ensure_infrastructure_permissions() -> None:
    """Sync station and railway-line permissions onto the three role groups.

    Idempotent. Missing Permission rows raise ``RuntimeError``.
    """
    for model in ("station", "railwayline"):
        try:
            content_type = ContentType.objects.get(app_label="infrastructure", model=model)
        except ContentType.DoesNotExist as exc:
            raise RuntimeError(
                f"ContentType for infrastructure.{model} is missing. Run migrations first."
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
                missing_display = ", ".join(f"infrastructure.{codename}" for codename in missing)
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


class ViewStationRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW_STATION
    raise_exception = True


class AddStationRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_ADD_STATION
    raise_exception = True


class ChangeStationRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_CHANGE_STATION
    raise_exception = True


class ViewRailwayLineRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW_RAILWAY_LINE
    raise_exception = True


class AddRailwayLineRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_ADD_RAILWAY_LINE
    raise_exception = True


class ChangeRailwayLineRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_CHANGE_RAILWAY_LINE
    raise_exception = True
