from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.accounts.permissions import require_authenticated_user
from apps.incidents.api.serializers import (
    IncidentDetailSerializer,
    IncidentSerializer,
    IncidentTransitionSerializer,
)
from apps.incidents.models import Incident
from apps.incidents.permissions import (
    PERM_ADD_INCIDENT,
    PERM_CHANGE_INCIDENT,
    PERM_VIEW_INCIDENT,
)
from apps.incidents.selectors import incident_directory, incident_with_history
from apps.incidents.services import (
    assign_incident,
    create_incident,
    transition_incident,
    update_incident,
)
from config.api.permissions import require_django_perm


class IncidentViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    http_method_names = ["get", "post", "patch", "head", "options"]
    search_fields = ["title", "description", "station__name", "station__code"]
    filterset_fields = ["status", "severity", "category", "station"]
    ordering_fields = ["reported_at", "updated_at", "severity", "status"]

    def get_queryset(self) -> QuerySet[Incident]:
        if self.action == "retrieve":
            return Incident.objects.select_related(
                "station",
                "railway_line",
                "reporter",
                "assigned_to",
            ).prefetch_related("events__actor")
        search = self.request.query_params.get("q") or self.request.query_params.get("search") or ""
        return incident_directory(search=search)

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        if self.action == "retrieve":
            return IncidentDetailSerializer
        if self.action == "transition":
            return IncidentTransitionSerializer
        return IncidentSerializer

    def get_permissions(self) -> list[BasePermission]:
        if self.action in {"list", "retrieve"}:
            perm = PERM_VIEW_INCIDENT
        elif self.action == "create":
            perm = PERM_ADD_INCIDENT
        else:
            perm = PERM_CHANGE_INCIDENT
        return [IsAuthenticated(), require_django_perm(perm)()]

    def perform_create(self, serializer: BaseSerializer[Incident]) -> None:
        actor = require_authenticated_user(self.request.user)
        data = serializer.validated_data
        incident = create_incident(
            actor=actor,
            title=data["title"],
            description=data["description"],
            station=data["station"],
            category=data["category"],
            severity=data["severity"],
            railway_line=data.get("railway_line"),
        )
        assigned = data.get("assigned_to")
        if assigned is not None:
            incident = assign_incident(actor=actor, incident_id=incident.pk, assignee=assigned)
        serializer.instance = incident

    def perform_update(self, serializer: BaseSerializer[Incident]) -> None:
        actor = require_authenticated_user(self.request.user)
        incident: Incident = serializer.instance  # type: ignore[assignment]
        data = serializer.validated_data
        updated = update_incident(
            actor=actor,
            incident_id=incident.pk,
            title=data.get("title", incident.title),
            description=data.get("description", incident.description),
            station=data.get("station", incident.station),
            category=data.get("category", incident.category),
            severity=data.get("severity", incident.severity),
            railway_line=data.get("railway_line", incident.railway_line),
        )
        if "assigned_to" in data:
            updated = assign_incident(
                actor=actor,
                incident_id=updated.pk,
                assignee=data["assigned_to"],
            )
        serializer.instance = updated

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request: Request, pk: object | None = None) -> Response:
        serializer = IncidentTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = require_authenticated_user(request.user)
        incident = transition_incident(
            incident_id=self.get_object().pk,
            new_status=Incident.Status(serializer.validated_data["status"]),
            actor=actor,
            comment=serializer.validated_data.get("comment") or None,
        )
        return Response(IncidentDetailSerializer(incident_with_history(incident.pk)).data)
