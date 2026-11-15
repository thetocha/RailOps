"""Timetable admin is superuser-only and view-oriented."""

from django.contrib import admin
from django.http import HttpRequest

from apps.timetables.models import Delay, ScheduledStop, TrainService


def _is_superuser(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return bool(user is not None and user.is_authenticated and user.is_superuser)


class SuperuserReadAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
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


class ScheduledStopInline(admin.TabularInline):  # type: ignore[type-arg]
    model = ScheduledStop
    extra = 0
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False


@admin.register(TrainService)
class TrainServiceAdmin(SuperuserReadAdmin):
    list_display = ("train_number", "service_date", "origin", "destination", "source")
    list_filter = ("source", "service_date")
    search_fields = ("train_number", "external_id")
    inlines = [ScheduledStopInline]


@admin.register(Delay)
class DelayAdmin(SuperuserReadAdmin):
    list_display = ("train_service", "kind", "delay_seconds", "recorded_at")
