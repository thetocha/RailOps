from __future__ import annotations

from rest_framework import serializers

from apps.infrastructure.models import Station


class StationSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)

    class Meta:
        model = Station
        fields = (
            "id",
            "name",
            "code",
            "city",
            "latitude",
            "longitude",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
