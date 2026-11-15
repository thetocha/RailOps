"""HTML forms for incidents. Event history is not editable."""

from __future__ import annotations

from typing import Any, cast

from django import forms
from django.db.models import Q, QuerySet

from apps.accounts.forms import apply_bootstrap
from apps.accounts.models import User
from apps.incidents.models import Incident
from apps.infrastructure.models import RailwayLine, Station


def _station_queryset(*, current_id: object | None = None) -> QuerySet[Station]:
    queryset = Station.objects.filter(is_active=True)
    if current_id is not None:
        queryset = Station.objects.filter(Q(is_active=True) | Q(pk=current_id))
    return queryset.order_by("name", "code")


def _line_queryset(*, current_id: object | None = None) -> QuerySet[RailwayLine]:
    queryset = RailwayLine.objects.filter(is_active=True)
    if current_id is not None:
        queryset = RailwayLine.objects.filter(Q(is_active=True) | Q(pk=current_id))
    return queryset.select_related("start_station", "end_station").order_by("name", "code")


class IncidentForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = Incident
        fields = ("title", "description", "station", "railway_line", "category", "severity")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        current_station = self.instance.station_id if self.instance.pk else None
        current_line = self.instance.railway_line_id if self.instance.pk else None
        station_field = cast(forms.ModelChoiceField, self.fields["station"])  # type: ignore[type-arg]
        line_field = cast(forms.ModelChoiceField, self.fields["railway_line"])  # type: ignore[type-arg]
        station_field.queryset = _station_queryset(current_id=current_station)
        line_field.queryset = _line_queryset(current_id=current_line)
        line_field.required = False
        apply_bootstrap(self)

    def clean_title(self) -> str:
        title = (self.cleaned_data.get("title") or "").strip()
        if not title:
            raise forms.ValidationError("Title is required.")
        return title

    def clean_description(self) -> str:
        description = (self.cleaned_data.get("description") or "").strip()
        if not description:
            raise forms.ValidationError("Description is required.")
        return description

    def clean_station(self) -> Station:
        station = cast(Station, self.cleaned_data["station"])
        if not station.is_active and (
            not self.instance.pk or self.instance.station_id != station.pk
        ):
            raise forms.ValidationError("Choose an active station.")
        return station


class IncidentTransitionForm(forms.Form):
    new_status = forms.ChoiceField(choices=())
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Optional note recorded in the incident history.",
    )

    def __init__(self, *args: Any, allowed_statuses: list[Incident.Status], **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        status_field = cast(forms.ChoiceField, self.fields["new_status"])
        status_field.choices = [(status.value, status.label) for status in allowed_statuses]
        apply_bootstrap(self)


class IncidentAssignForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        help_text="Leave empty to unassign.",
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(
        self,
        *args: Any,
        current_assignee: User | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        assigned_field = cast(forms.ModelChoiceField, self.fields["assigned_to"])  # type: ignore[type-arg]
        queryset = User.objects.filter(is_active=True)
        if current_assignee is not None and current_assignee.pk:
            queryset = User.objects.filter(Q(is_active=True) | Q(pk=current_assignee.pk))
        assigned_field.queryset = queryset.order_by("username")
        apply_bootstrap(self)


class IncidentSeverityForm(forms.Form):
    severity = forms.ChoiceField(choices=Incident.Severity.choices)
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        apply_bootstrap(self)
