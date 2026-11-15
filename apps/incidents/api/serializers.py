from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import User
from apps.incidents.models import Incident, IncidentEvent
from apps.infrastructure.models import RailwayLine, Station


class IncidentEventSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    actor = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = IncidentEvent
        fields = (
            "id",
            "event_type",
            "previous_status",
            "new_status",
            "description",
            "actor",
            "created_at",
        )
        read_only_fields = fields


class IncidentSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    station = serializers.PrimaryKeyRelatedField(queryset=Station.objects.all())
    railway_line = serializers.PrimaryKeyRelatedField(
        queryset=RailwayLine.objects.all(),
        allow_null=True,
        required=False,
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )
    reporter = serializers.CharField(source="reporter.username", read_only=True)
    station_code = serializers.CharField(source="station.code", read_only=True)

    class Meta:
        model = Incident
        fields: tuple[str, ...] = (
            "id",
            "title",
            "description",
            "station",
            "station_code",
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
        read_only_fields = (
            "id",
            "status",
            "reporter",
            "reported_at",
            "updated_at",
            "resolved_at",
            "station_code",
        )


class IncidentDetailSerializer(IncidentSerializer):
    events = IncidentEventSerializer(many=True, read_only=True)

    class Meta(IncidentSerializer.Meta):
        fields: tuple[str, ...] = (*IncidentSerializer.Meta.fields, "events")


class IncidentTransitionSerializer(serializers.Serializer):  # type: ignore[type-arg]
    status = serializers.ChoiceField(choices=Incident.Status.choices)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
