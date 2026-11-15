from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.serializers import BaseSerializer

from apps.accounts.permissions import require_authenticated_user
from apps.infrastructure.api.serializers import StationSerializer
from apps.infrastructure.geo import point_from_lon_lat
from apps.infrastructure.models import Station
from apps.infrastructure.permissions import (
    PERM_ADD_STATION,
    PERM_CHANGE_STATION,
    PERM_VIEW_STATION,
)
from apps.infrastructure.selectors import station_directory
from apps.infrastructure.services import create_station, update_station
from config.api.permissions import require_django_perm


class StationViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = StationSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    search_fields = ["name", "code", "city"]
    filterset_fields = ["is_active"]
    ordering_fields = ["name", "code", "city", "created_at"]

    def get_queryset(self) -> QuerySet[Station]:
        search = self.request.query_params.get("q") or self.request.query_params.get("search") or ""
        return station_directory(search=search, is_active=None)

    def get_permissions(self) -> list[BasePermission]:
        if self.action in {"list", "retrieve"}:
            perm = PERM_VIEW_STATION
        elif self.action == "create":
            perm = PERM_ADD_STATION
        else:
            perm = PERM_CHANGE_STATION
        return [IsAuthenticated(), require_django_perm(perm)()]

    def perform_create(self, serializer: BaseSerializer[Station]) -> None:
        actor = require_authenticated_user(self.request.user)
        data = serializer.validated_data
        station = create_station(
            actor=actor,
            name=data["name"],
            code=data["code"],
            city=data["city"],
            location=point_from_lon_lat(data["longitude"], data["latitude"]),
            is_active=data.get("is_active", True),
        )
        serializer.instance = station

    def perform_update(self, serializer: BaseSerializer[Station]) -> None:
        actor = require_authenticated_user(self.request.user)
        station: Station = serializer.instance  # type: ignore[assignment]
        data = serializer.validated_data
        latitude = data.get("latitude", station.latitude)
        longitude = data.get("longitude", station.longitude)
        updated = update_station(
            actor=actor,
            station=station,
            name=data.get("name", station.name),
            code=data.get("code", station.code),
            city=data.get("city", station.city),
            location=point_from_lon_lat(longitude, latitude),
            is_active=data.get("is_active", station.is_active),
        )
        serializer.instance = updated
