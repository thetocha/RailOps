"""Report permission helpers. Views must not branch on role group names."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER

PERM_VIEW_REPORT = "reports.view_report"
PERM_ADD_REPORT = "reports.add_report"

_MANAGED = frozenset({"view_report", "add_report", "change_report", "delete_report"})
_ADMIN = frozenset({"view_report", "add_report"})

PERMISSION_CODENAMES_BY_GROUP: dict[str, frozenset[str]] = {
    GROUP_ADMINISTRATOR: _ADMIN,
    GROUP_DISPATCHER: frozenset(),
    GROUP_VIEWER: frozenset(),
}


def can_view_reports(user: object) -> bool:
    return (
        isinstance(user, AbstractUser) and user.is_authenticated and user.has_perm(PERM_VIEW_REPORT)
    )


def can_add_reports(user: object) -> bool:
    return (
        isinstance(user, AbstractUser) and user.is_authenticated and user.has_perm(PERM_ADD_REPORT)
    )


@transaction.atomic
def ensure_report_permissions() -> None:
    """Sync report permissions onto the three role groups. Idempotent."""
    try:
        content_type = ContentType.objects.get(app_label="reports", model="report")
    except ContentType.DoesNotExist as exc:
        raise RuntimeError(
            "ContentType for reports.report is missing. Run migrations first."
        ) from exc
    permissions = list(Permission.objects.filter(content_type=content_type, codename__in=_MANAGED))
    by_codename = {permission.codename: permission for permission in permissions}
    missing = sorted(_MANAGED - by_codename.keys())
    if missing:
        missing_display = ", ".join(f"reports.{codename}" for codename in missing)
        raise RuntimeError(
            f"Missing permission(s) {missing_display}. Run migrations so Django can create them."
        )
    for group_name, expected in PERMISSION_CODENAMES_BY_GROUP.items():
        group, _created = Group.objects.get_or_create(name=group_name)
        if expected:
            group.permissions.add(*(by_codename[codename] for codename in expected))
        stale = group.permissions.filter(
            content_type=content_type,
            codename__in=_MANAGED - expected,
        )
        if stale.exists():
            group.permissions.remove(*stale)


class ViewReportRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW_REPORT
    raise_exception = True


class AddReportRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_ADD_REPORT
    raise_exception = True
