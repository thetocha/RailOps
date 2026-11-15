"""Analytics permission helpers. Views must not branch on role group names."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER

PERM_VIEW_ANALYTICS = "analytics.view_operationalanalytics"

_MANAGED = frozenset({"view_operationalanalytics"})

PERMISSION_CODENAMES_BY_GROUP: dict[str, frozenset[str]] = {
    GROUP_ADMINISTRATOR: _MANAGED,
    GROUP_DISPATCHER: _MANAGED,
    GROUP_VIEWER: _MANAGED,
}


def can_view_analytics(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_VIEW_ANALYTICS)
    )


@transaction.atomic
def ensure_analytics_permissions() -> None:
    """Sync analytics permissions onto the three role groups. Idempotent."""
    try:
        content_type = ContentType.objects.get(
            app_label="analytics",
            model="operationalanalytics",
        )
    except ContentType.DoesNotExist as exc:
        raise RuntimeError(
            "ContentType for analytics.operationalanalytics is missing. Run migrations first."
        ) from exc
    permissions = list(Permission.objects.filter(content_type=content_type, codename__in=_MANAGED))
    by_codename = {permission.codename: permission for permission in permissions}
    missing = sorted(_MANAGED - by_codename.keys())
    if missing:
        missing_display = ", ".join(f"analytics.{codename}" for codename in missing)
        raise RuntimeError(
            f"Missing permission(s) {missing_display}. Run migrations so Django can create them."
        )
    for group_name, expected in PERMISSION_CODENAMES_BY_GROUP.items():
        group, _created = Group.objects.get_or_create(name=group_name)
        group.permissions.add(*(by_codename[codename] for codename in expected))
        stale = group.permissions.filter(
            content_type=content_type,
            codename__in=_MANAGED - expected,
        )
        if stale.exists():
            group.permissions.remove(*stale)


class ViewAnalyticsRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW_ANALYTICS
    raise_exception = True
