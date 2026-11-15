"""Timetable permission helpers. Views must not branch on role group names."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER

PERM_VIEW_TRAIN_SERVICE = "timetables.view_trainservice"
PERM_VIEW_DELAY = "timetables.view_delay"

_SERVICE_MANAGED = frozenset(
    {"view_trainservice", "add_trainservice", "change_trainservice", "delete_trainservice"}
)
_STOP_MANAGED = frozenset(
    {"view_scheduledstop", "add_scheduledstop", "change_scheduledstop", "delete_scheduledstop"}
)
_DELAY_MANAGED = frozenset({"view_delay", "add_delay", "change_delay", "delete_delay"})

_READ_SERVICE = frozenset({"view_trainservice"})
_READ_STOP = frozenset({"view_scheduledstop"})
_READ_DELAY = frozenset({"view_delay"})

PERMISSION_CODENAMES_BY_GROUP: dict[str, dict[str, frozenset[str]]] = {
    GROUP_ADMINISTRATOR: {
        "trainservice": _READ_SERVICE,
        "scheduledstop": _READ_STOP,
        "delay": _READ_DELAY,
    },
    GROUP_DISPATCHER: {
        "trainservice": _READ_SERVICE,
        "scheduledstop": _READ_STOP,
        "delay": _READ_DELAY,
    },
    GROUP_VIEWER: {
        "trainservice": _READ_SERVICE,
        "scheduledstop": _READ_STOP,
        "delay": _READ_DELAY,
    },
}

_MANAGED_BY_MODEL: dict[str, frozenset[str]] = {
    "trainservice": _SERVICE_MANAGED,
    "scheduledstop": _STOP_MANAGED,
    "delay": _DELAY_MANAGED,
}


def can_view_train_services(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_VIEW_TRAIN_SERVICE)
    )


@transaction.atomic
def ensure_timetable_permissions() -> None:
    for model in ("trainservice", "scheduledstop", "delay"):
        try:
            content_type = ContentType.objects.get(app_label="timetables", model=model)
        except ContentType.DoesNotExist as exc:
            raise RuntimeError(
                f"ContentType for timetables.{model} is missing. Run migrations first."
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
                missing_display = ", ".join(f"timetables.{codename}" for codename in missing)
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


class ViewTrainServiceRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW_TRAIN_SERVICE
    raise_exception = True
