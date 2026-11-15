from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from apps.accounts.models import User
from apps.analytics.permissions import PERM_VIEW_ANALYTICS
from apps.analytics.tests.conftest import TEST_PASSWORD, redirect_location
from apps.incidents.models import Incident
from apps.incidents.services import create_incident
from apps.infrastructure.models import Station

pytestmark = pytest.mark.django_db


def test_unauthenticated_analytics_redirects_to_login(client: Client) -> None:
    response = client.get("/analytics/")
    assert response.status_code == 302
    assert "/accounts/login/" in redirect_location(response)


def test_viewer_can_open_analytics_empty_state(client: Client, viewer: User) -> None:
    client.force_login(viewer)
    response = client.get("/analytics/")
    assert response.status_code == 200
    assert b"No incidents were reported in this period." in response.content
    assert b"No train services were imported for this period." in response.content
    assert b"On-time means delay of 300 seconds" in response.content


def test_invalid_period_shows_errors_and_does_not_query(
    client: Client,
    dispatcher: User,
    berlin: Station,
) -> None:
    create_incident(
        actor=dispatcher,
        title="Should not leak into invalid period",
        description="Still there, but the form is invalid.",
        station=berlin,
        category=Incident.Category.OTHER,
        severity=Incident.Severity.LOW,
    )
    client.force_login(dispatcher)
    response = client.get(
        "/analytics/",
        {"period_start": "2026-02-10", "period_end": "2026-02-01"},
    )
    assert response.status_code == 200
    assert b"Start date must be on or before the end date." in response.content
    assert response.context["overview"] is None


def test_filtered_period_shows_incident_counts(
    client: Client,
    viewer: User,
    dispatcher: User,
    berlin: Station,
) -> None:
    create_incident(
        actor=dispatcher,
        title="Visible incident",
        description="In range once dates are updated.",
        station=berlin,
        category=Incident.Category.TECHNICAL_FAILURE,
        severity=Incident.Severity.CRITICAL,
    )
    Incident.objects.update(reported_at=datetime(2026, 10, 5, 12, 0, tzinfo=UTC))
    client.force_login(viewer)
    response = client.get(
        "/analytics/",
        {"period_start": "2026-10-01", "period_end": "2026-10-31"},
    )
    assert response.status_code == 200
    overview = response.context["overview"]
    assert overview is not None
    assert overview.incidents.total == 1
    assert overview.incidents.by_severity[3].key == Incident.Severity.CRITICAL
    assert overview.incidents.by_severity[3].count == 1
    assert b"Critical" in response.content


def test_user_without_analytics_permission_is_forbidden(client: Client, db: None) -> None:
    user = User.objects.create_user(
        username="no_analytics",
        email="no_analytics@example.com",
        password=TEST_PASSWORD,
    )
    user.user_permissions.add(
        Permission.objects.get(codename="access_dashboard", content_type__app_label="accounts")
    )
    client.force_login(user)
    response = client.get("/analytics/")
    assert response.status_code == 403
    assert not user.has_perm(PERM_VIEW_ANALYTICS)
