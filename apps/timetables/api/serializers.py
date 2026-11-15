from __future__ import annotations

from rest_framework import serializers

from apps.timetables.models import Delay, ScheduledStop, TrainService


class DelaySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Delay
        fields = ("id", "kind", "delay_seconds", "recorded_at", "source")
        read_only_fields = fields


class ScheduledStopSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    station_code = serializers.CharField(source="station.code", read_only=True)
    delays = DelaySerializer(source="delay_records", many=True, read_only=True)

    class Meta:
        model = ScheduledStop
        fields = (
            "id",
            "stop_sequence",
            "station",
            "station_code",
            "scheduled_arrival",
            "scheduled_departure",
            "actual_arrival",
            "actual_departure",
            "delays",
        )
        read_only_fields = fields


class TrainServiceSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    origin_code = serializers.CharField(source="origin.code", read_only=True)
    destination_code = serializers.CharField(source="destination.code", read_only=True)

    class Meta:
        model = TrainService
        fields: tuple[str, ...] = (
            "id",
            "external_id",
            "train_number",
            "origin",
            "origin_code",
            "destination",
            "destination_code",
            "service_date",
            "source",
            "imported_at",
        )
        read_only_fields = fields


class TrainServiceDetailSerializer(TrainServiceSerializer):
    stops = ScheduledStopSerializer(many=True, read_only=True)

    class Meta(TrainServiceSerializer.Meta):
        fields: tuple[str, ...] = (*TrainServiceSerializer.Meta.fields, "stops")
