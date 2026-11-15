from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from django.db.models import QuerySet
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.timetables.api.serializers import (
    ScheduledStopSerializer,
    TrainServiceDetailSerializer,
    TrainServiceSerializer,
)
from apps.timetables.models import TrainService
from apps.timetables.permissions import PERM_VIEW_TRAIN_SERVICE
from apps.timetables.selectors import stops_for_service, train_service_directory
from config.api.permissions import require_django_perm


class TrainServiceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    http_method_names = ["get", "head", "options"]
    search_fields = ["train_number", "external_id"]
    ordering_fields = ["service_date", "train_number", "imported_at"]

    def get_queryset(self) -> QuerySet[TrainService]:
        service_date_raw = self.request.query_params.get("date") or self.request.query_params.get(
            "service_date"
        )
        service_date: date | None = None
        if service_date_raw:
            try:
                service_date = date.fromisoformat(service_date_raw)
            except ValueError:
                service_date = None
        station_raw = self.request.query_params.get("station")
        station_id: UUID | None = None
        if station_raw:
            try:
                station_id = UUID(station_raw)
            except ValueError:
                station_id = None
        return train_service_directory(
            service_date=service_date,
            station_id=station_id,
            train_number=self.request.query_params.get("q")
            or self.request.query_params.get("search")
            or "",
        )

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        if self.action == "retrieve":
            return TrainServiceDetailSerializer
        return TrainServiceSerializer

    def get_permissions(self) -> list[BasePermission]:
        return [IsAuthenticated(), require_django_perm(PERM_VIEW_TRAIN_SERVICE)()]

    def retrieve(self, request: Request, *args: object, **kwargs: object) -> Response:
        service: TrainService = self.get_object()
        serializer = TrainServiceDetailSerializer(service)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="stops")
    def stops(self, request: Request, pk: object | None = None) -> Response:
        service: TrainService = self.get_object()
        serializer = ScheduledStopSerializer(stops_for_service(service), many=True)
        return Response(serializer.data)
