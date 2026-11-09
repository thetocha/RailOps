"""Role groups and permission helpers.

Authorization in views and services must call these helpers or
``user.has_perm(...)``. Do not branch on group names in views.

Groups are created by ``ensure_role_groups``, invoked from the accounts
``post_migrate`` signal and the ``seed_role_groups`` management command.

Later apps should attach their own model permissions to the same groups in
their own ``post_migrate`` handlers. This module only adds or removes
permissions whose content type is ``accounts.user``, so incident/station
permissions added later are left intact.
"""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet

from apps.accounts.models import User

GROUP_ADMINISTRATOR = "Administrator"
GROUP_DISPATCHER = "Dispatcher"
GROUP_VIEWER = "Viewer"

ROLE_GROUP_NAMES: tuple[str, ...] = (
    GROUP_ADMINISTRATOR,
    GROUP_DISPATCHER,
    GROUP_VIEWER,
)

PERM_MANAGE_USERS = "accounts.manage_users"
PERM_ACCESS_DASHBOARD = "accounts.access_dashboard"
PERM_VIEW_OPERATIONS = "accounts.view_operations"
PERM_CHANGE_OPERATIONS = "accounts.change_operations"

# Built-in and custom User permissions this module is allowed to add or revoke
# on the three role groups. Permissions on other content types are never touched.
_MANAGED_USER_CODENAMES: frozenset[str] = frozenset(
    {
        "manage_users",
        "access_dashboard",
        "view_operations",
        "change_operations",
        "view_user",
        "add_user",
        "change_user",
        "delete_user",
    }
)

PERMISSION_CODENAMES_BY_GROUP: dict[str, frozenset[str]] = {
    GROUP_ADMINISTRATOR: frozenset(
        {
            "manage_users",
            "access_dashboard",
            "view_operations",
            "change_operations",
            "view_user",
            "add_user",
            "change_user",
        }
    ),
    GROUP_DISPATCHER: frozenset(
        {
            "access_dashboard",
            "view_operations",
            "change_operations",
        }
    ),
    GROUP_VIEWER: frozenset(
        {
            "access_dashboard",
            "view_operations",
        }
    ),
}


def can_manage_users(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_MANAGE_USERS)
    )


def can_access_dashboard(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_ACCESS_DASHBOARD)
    )


def can_view_operations(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_VIEW_OPERATIONS)
    )


def can_change_operations(user: object) -> bool:
    return (
        isinstance(user, AbstractUser)
        and user.is_authenticated
        and user.has_perm(PERM_CHANGE_OPERATIONS)
    )


def require_authenticated_user(user: object) -> User:
    if not isinstance(user, User) or not user.is_authenticated:
        raise PermissionDenied
    return user


def role_group_queryset() -> QuerySet[Group]:
    return Group.objects.filter(name__in=ROLE_GROUP_NAMES).order_by("name")


@transaction.atomic
def ensure_role_groups() -> None:
    """Create the three role groups and sync accounts.user permissions.

    Idempotent. Missing Permission rows raise ``RuntimeError`` (never swallowed).
    Permissions on other apps/models are preserved.
    """
    try:
        content_type = ContentType.objects.get(app_label="accounts", model="user")
    except ContentType.DoesNotExist as exc:
        raise RuntimeError(
            "ContentType for accounts.user is missing. Run migrations first."
        ) from exc

    managed = list(
        Permission.objects.filter(content_type=content_type, codename__in=_MANAGED_USER_CODENAMES)
    )
    managed_by_codename = {permission.codename: permission for permission in managed}

    for group_name, expected_codenames in PERMISSION_CODENAMES_BY_GROUP.items():
        missing = sorted(expected_codenames - managed_by_codename.keys())
        if missing:
            missing_display = ", ".join(f"accounts.{codename}" for codename in missing)
            raise RuntimeError(
                "Missing permission(s) "
                f"{missing_display}. Run migrations so Django can create them."
            )
        group, _created = Group.objects.get_or_create(name=group_name)
        to_add = [managed_by_codename[codename] for codename in expected_codenames]
        group.permissions.add(*to_add)
        stale = group.permissions.filter(
            content_type=content_type,
            codename__in=_MANAGED_USER_CODENAMES - expected_codenames,
        )
        if stale.exists():
            group.permissions.remove(*stale)


def assign_administrator_group_to_superusers() -> int:
    """Attach the Administrator group to superusers that are not already members."""
    group, _created = Group.objects.get_or_create(name=GROUP_ADMINISTRATOR)
    assigned = 0
    superusers = User.objects.filter(is_superuser=True).prefetch_related("groups")
    for user in superusers:
        if not user.groups.filter(pk=group.pk).exists():
            user.groups.add(group)
            assigned += 1
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])
    return assigned


class DashboardAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_ACCESS_DASHBOARD
    raise_exception = True


class ManageUsersRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_MANAGE_USERS
    raise_exception = True
