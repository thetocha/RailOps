from __future__ import annotations

from typing import cast

import pytest
from django.forms import ModelChoiceField

from apps.infrastructure.forms import RailwayLineForm, StationForm
from apps.infrastructure.models import Station

pytestmark = pytest.mark.django_db


def _station_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Munich Hbf",
        "code": "mhbf",
        "city": "Munich",
        "latitude": "48.140228",
        "longitude": "11.558337",
        "is_active": "on",
    }
    payload.update(overrides)
    return payload


def test_station_form_builds_point_and_uppercases_code() -> None:
    form = StationForm(_station_payload())
    assert form.is_valid(), form.errors
    assert form.cleaned_data["code"] == "MHBF"
    assert form.cleaned_data["location"].x == pytest.approx(11.558337)
    assert form.cleaned_data["location"].y == pytest.approx(48.140228)


def test_station_form_rejects_invalid_latitude() -> None:
    form = StationForm(_station_payload(latitude="95"))
    assert not form.is_valid()
    assert "latitude" in form.errors


def test_station_form_rejects_duplicate_code(berlin: Station) -> None:
    form = StationForm(_station_payload(code="BHF", name="Copy", city="Berlin"))
    assert not form.is_valid()
    assert "code" in form.errors


def test_station_form_rejects_invalid_code_characters() -> None:
    form = StationForm(_station_payload(code="bad code!"))
    assert not form.is_valid()
    assert "code" in form.errors


def test_line_form_excludes_inactive_stations_on_create(berlin: Station, hamburg: Station) -> None:
    hamburg.is_active = False
    hamburg.save(update_fields=["is_active"])
    form = RailwayLineForm()
    start_field = cast("ModelChoiceField[Station]", form.fields["start_station"])
    queryset = start_field.queryset
    assert queryset is not None
    station_ids = set(queryset.values_list("pk", flat=True))
    assert berlin.pk in station_ids
    assert hamburg.pk not in station_ids
