"""Integration permission helpers."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER

PERM_VIEW_SYNC_RUN = "integrations.view_externalsyncrun"
PERM_RUN_SYNC = "integrations.run_timetable_sync"

_RUN_MANAGED = frozenset(
    {
        "view_externalsyncrun",
        "add_externalsyncrun",
        "change_externalsyncrun",
        "delete_externalsyncrun",
        "run_timetable_sync",
    }
)

PERMISSION_CODENAMES_BY_GROUP: dict[str, frozenset[str]] = {
    GROUP_ADMINISTRATOR: frozenset({"view_externalsyncrun", "run_timetable_sync"}),
    GROUP_DISPATCHER: frozenset(),
    GROUP_VIEWER: frozenset(),
}


def can_run_timetable_sync(user: object) -> bool:
    return isinstance(user, AbstractUser) and user.is_authenticated and user.has_perm(PERM_RUN_SYNC)


@transaction.atomic
def ensure_integration_permissions() -> None:
    try:
        content_type = ContentType.objects.get(app_label="integrations", model="externalsyncrun")
    except ContentType.DoesNotExist as exc:
        raise RuntimeError(
            "ContentType for integrations.externalsyncrun is missing. Run migrations first."
        ) from exc
    permissions = list(
        Permission.objects.filter(content_type=content_type, codename__in=_RUN_MANAGED)
    )
    by_codename = {permission.codename: permission for permission in permissions}
    for group_name, expected in PERMISSION_CODENAMES_BY_GROUP.items():
        missing = sorted(expected - by_codename.keys())
        if missing:
            missing_display = ", ".join(f"integrations.{codename}" for codename in missing)
            raise RuntimeError(
                "Missing permission(s) "
                f"{missing_display}. Run migrations so Django can create them."
            )
        group, _created = Group.objects.get_or_create(name=group_name)
        to_add = [by_codename[codename] for codename in expected]
        if to_add:
            group.permissions.add(*to_add)
        stale = group.permissions.filter(
            content_type=content_type,
            codename__in=_RUN_MANAGED - expected,
        )
        if stale.exists():
            group.permissions.remove(*stale)


class ViewSyncRunRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW_SYNC_RUN
    raise_exception = True


class RunSyncRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_RUN_SYNC
    raise_exception = True
