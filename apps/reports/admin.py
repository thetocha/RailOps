"""Report admin is superuser-only and read-only."""

from django.contrib import admin
from django.http import HttpRequest

from apps.reports.models import Report


def _is_superuser(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return bool(user is not None and user.is_authenticated and user.is_superuser)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "report_type", "period_start", "period_end", "status", "requested_by")
    readonly_fields = (
        "id",
        "report_type",
        "period_start",
        "period_end",
        "requested_by",
        "status",
        "generated_at",
        "file",
        "error_summary",
        "created_at",
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
