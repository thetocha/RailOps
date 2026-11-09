"""Django admin is reserved for superusers.

Role-based Administrators manage users through the application Users UI.
Staff accounts that are not superusers must not be able to assign groups,
user_permissions, is_staff, or is_superuser via /admin/.
"""

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.http import HttpRequest

from apps.accounts.models import User


def _is_superuser(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return bool(user is not None and user.is_authenticated and user.is_superuser)


def _admin_has_permission(request: HttpRequest) -> bool:
    return bool(_is_superuser(request) and request.user.is_active)


admin.site.has_permission = _admin_has_permission  # type: ignore[method-assign]


class SuperuserAdminMixin:
    """Block add/change/delete/view for anyone who is not a superuser."""

    def has_module_permission(self, request: HttpRequest) -> bool:
        return _is_superuser(request)

    def has_view_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return _is_superuser(request)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return _is_superuser(request)

    def has_change_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return _is_superuser(request)

    def has_delete_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return _is_superuser(request)


@admin.register(User)
class UserAdmin(SuperuserAdminMixin, DjangoUserAdmin):  # type: ignore[type-arg]
    list_display = ("username", "email", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff", "groups")
    readonly_fields = (*DjangoUserAdmin.readonly_fields, "created_at", "updated_at")
    ordering = ("username",)


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(SuperuserAdminMixin, DjangoGroupAdmin):
    """Role-group permission edits are superuser-only; seed_role_groups restores them."""
