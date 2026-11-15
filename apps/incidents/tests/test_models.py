from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from apps.accounts.models import User
from apps.incidents.models import Incident, IncidentEvent
from apps.infrastructure.models import Station

pytestmark = pytest.mark.django_db


def test_incident_defaults_and_str(open_incident: Incident) -> None:
    assert open_incident.status == Incident.Status.OPEN
    assert open_incident.resolved_at is None
    assert open_incident.reported_at <= timezone.now()
    assert "Signal failure at Berlin" in str(open_incident)


def test_station_delete_is_protected_when_incident_exists(
    open_incident: Incident,
    berlin: Station,
) -> None:
    with pytest.raises(ProtectedError), transaction.atomic():
        berlin.delete()
    assert Station.objects.filter(pk=berlin.pk).exists()
    assert Incident.objects.filter(pk=open_incident.pk).exists()


def test_empty_title_is_rejected(dispatcher: User, berlin: Station) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Incident.objects.create(
            title="",
            description="x",
            station=berlin,
            category=Incident.Category.OTHER,
            severity=Incident.Severity.LOW,
            reporter=dispatcher,
        )


def test_resolved_at_check_constraint(open_incident: Incident) -> None:
    open_incident.resolved_at = timezone.now()
    with pytest.raises(IntegrityError), transaction.atomic():
        open_incident.save(update_fields=["resolved_at"])


def test_incident_event_is_immutable(open_incident: Incident, dispatcher: User) -> None:
    event = open_incident.events.get()
    event.description = "tamper"
    with pytest.raises(ValidationError):
        event.save()
    with pytest.raises(ValidationError):
        event.delete()
    event.refresh_from_db()
    assert event.description == "Incident registered."
    assert IncidentEvent.objects.filter(pk=event.pk).exists()
