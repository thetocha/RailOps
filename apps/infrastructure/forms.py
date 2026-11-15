"""HTML forms for stations and railway lines."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from django import forms
from django.db.models import Q, QuerySet

from apps.accounts.forms import apply_bootstrap
from apps.infrastructure.codes import normalize_infrastructure_code
from apps.infrastructure.geo import point_from_lon_lat
from apps.infrastructure.models import RailwayLine, Station


class StationForm(forms.ModelForm):  # type: ignore[type-arg]
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
        help_text="WGS84 latitude in decimal degrees.",
    )
    longitude = forms.DecimalField(
        max_digits=10,
        decimal_places=6,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
        help_text="WGS84 longitude in decimal degrees.",
    )

    class Meta:
        model = Station
        fields = ("name", "code", "city", "is_active")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields[
            "code"
        ].help_text = "Unique operational code. Letters, digits, underscores, and hyphens."
        if self.instance.pk and self.instance.location:
            self.fields["latitude"].initial = f"{self.instance.latitude:.6f}"
            self.fields["longitude"].initial = f"{self.instance.longitude:.6f}"
        self.fields["is_active"].initial = True
        apply_bootstrap(self)

    def clean_code(self) -> str:
        return normalize_infrastructure_code(self.cleaned_data.get("code") or "")

    def clean_name(self) -> str:
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        return name

    def clean_city(self) -> str:
        city = (self.cleaned_data.get("city") or "").strip()
        if not city:
            raise forms.ValidationError("City is required.")
        return city

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        latitude = cleaned.get("latitude")
        longitude = cleaned.get("longitude")
        if latitude is not None and longitude is not None:
            cleaned["location"] = point_from_lon_lat(longitude, latitude)
        code = cleaned.get("code")
        if code:
            query = Station.objects.filter(code=code)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                self.add_error("code", "A station with this code already exists.")
        return cleaned


def _station_choices(*, instance: RailwayLine | None) -> QuerySet[Station]:
    queryset = Station.objects.filter(is_active=True)
    if instance is not None and instance.pk:
        queryset = Station.objects.filter(
            Q(is_active=True) | Q(pk__in=[instance.start_station_id, instance.end_station_id])
        )
    return queryset.order_by("name", "code")


class RailwayLineForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = RailwayLine
        fields = ("name", "code", "start_station", "end_station", "is_active")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        stations = _station_choices(instance=self.instance if self.instance.pk else None)
        start_field = cast(forms.ModelChoiceField, self.fields["start_station"])  # type: ignore[type-arg]
        end_field = cast(forms.ModelChoiceField, self.fields["end_station"])  # type: ignore[type-arg]
        start_field.queryset = stations
        end_field.queryset = stations
        self.fields[
            "code"
        ].help_text = "Unique operational code. Letters, digits, underscores, and hyphens."
        self.fields["is_active"].initial = True
        apply_bootstrap(self)

    def clean_code(self) -> str:
        return normalize_infrastructure_code(self.cleaned_data.get("code") or "")

    def clean_name(self) -> str:
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        return name

    def clean_start_station(self) -> Station:
        station = cast(Station, self.cleaned_data["start_station"])
        if not station.is_active and (
            not self.instance.pk or self.instance.start_station_id != station.pk
        ):
            raise forms.ValidationError("Choose an active start station.")
        return station

    def clean_end_station(self) -> Station:
        station = cast(Station, self.cleaned_data["end_station"])
        if not station.is_active and (
            not self.instance.pk or self.instance.end_station_id != station.pk
        ):
            raise forms.ValidationError("Choose an active end station.")
        return station

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        code = cleaned.get("code")
        if code:
            query = RailwayLine.objects.filter(code=code)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                self.add_error("code", "A railway line with this code already exists.")
        return cleaned
