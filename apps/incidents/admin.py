"""Incident admin is superuser-only. Event rows are read-only."""

from django.contrib import admin
from django.http import HttpRequest

from apps.incidents.models import Incident, IncidentEvent


def _is_superuser(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return bool(user is not None and user.is_authenticated and user.is_superuser)


class SuperuserAdminMixin:
    def has_module_permission(self, request: HttpRequest) -> bool:
        return _is_superuser(request)

    def has_view_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return _is_superuser(request)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return _is_superuser(request)

    def has_change_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return _is_superuser(request)

    def has_delete_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False


class IncidentEventInline(admin.TabularInline):  # type: ignore[type-arg]
    model = IncidentEvent
    extra = 0
    can_delete = False
    readonly_fields = (
        "actor",
        "event_type",
        "previous_status",
        "new_status",
        "description",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False


@admin.register(Incident)
class IncidentAdmin(SuperuserAdminMixin, admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("title", "station", "severity", "status", "reporter", "reported_at")
    list_filter = ("status", "severity", "category")
    search_fields = ("title", "description")
    readonly_fields = (
        "title",
        "description",
        "station",
        "railway_line",
        "category",
        "severity",
        "status",
        "reporter",
        "assigned_to",
        "reported_at",
        "updated_at",
        "resolved_at",
    )
    inlines = [IncidentEventInline]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False


@admin.register(IncidentEvent)
class IncidentEventAdmin(SuperuserAdminMixin, admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("incident", "event_type", "actor", "created_at")
    readonly_fields = (
        "incident",
        "actor",
        "event_type",
        "previous_status",
        "new_status",
        "description",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False
