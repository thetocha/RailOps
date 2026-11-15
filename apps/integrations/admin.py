"""Sync-run admin is superuser-only and read-only."""

from django.contrib import admin
from django.http import HttpRequest

from apps.integrations.models import ExternalSyncRun


def _is_superuser(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return bool(user is not None and user.is_authenticated and user.is_superuser)


@admin.register(ExternalSyncRun)
class ExternalSyncRunAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "integration_name",
        "status",
        "records_processed",
        "records_created",
        "records_updated",
        "started_at",
    )
    readonly_fields = (
        "integration_name",
        "started_at",
        "finished_at",
        "status",
        "records_processed",
        "records_created",
        "records_updated",
        "error_summary",
    )

    def has_module_permission(self, request: HttpRequest) -> bool:
        return _is_superuser(request)

    def has_view_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return _is_superuser(request)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False
