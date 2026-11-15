"""Infrastructure admin is superuser-only, matching the accounts lockdown."""

from django.contrib.gis import admin
from django.http import HttpRequest

from apps.infrastructure.models import RailwayLine, Station


def _is_superuser(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return bool(user is not None and user.is_authenticated and user.is_superuser)


class SuperuserGISAdmin(admin.GISModelAdmin):  # type: ignore[type-arg]
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


@admin.register(Station)
class StationAdmin(SuperuserGISAdmin):
    list_display = ("code", "name", "city", "is_active", "updated_at")
    list_filter = ("is_active", "city")
    search_fields = ("code", "name", "city")
    readonly_fields = ("created_at", "updated_at")


@admin.register(RailwayLine)
class RailwayLineAdmin(SuperuserGISAdmin):
    list_display = ("code", "name", "start_station", "end_station", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("start_station", "end_station")
