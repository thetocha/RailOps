from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from apps.accounts.models import User
from apps.reports.models import Report
from apps.reports.permissions import PERM_VIEW_REPORT
from apps.reports.tests.conftest import TEST_PASSWORD, redirect_location

pytestmark = pytest.mark.django_db


def test_unauthenticated_reports_redirect_to_login(client: Client) -> None:
    response = client.get("/reports/")
    assert response.status_code == 302
    assert "/accounts/login/" in redirect_location(response)


def test_dispatcher_cannot_open_reports(client: Client, dispatcher: User) -> None:
    client.force_login(dispatcher)
    assert client.get("/reports/").status_code == 403
    assert (
        client.post(
            "/reports/create/",
            {"period_start": "2026-11-01", "period_end": "2026-11-15"},
        ).status_code
        == 403
    )
    assert Report.objects.count() == 0


def test_viewer_cannot_open_reports(client: Client, viewer: User) -> None:
    client.force_login(viewer)
    assert client.get("/reports/").status_code == 403


def test_user_without_report_permission_is_forbidden(client: Client, db: None) -> None:
    user = User.objects.create_user(
        username="no_reports",
        email="no_reports@example.com",
        password=TEST_PASSWORD,
    )
    user.user_permissions.add(
        Permission.objects.get(codename="access_dashboard", content_type__app_label="accounts")
    )
    client.force_login(user)
    response = client.get("/reports/")
    assert response.status_code == 403
    assert not user.has_perm(PERM_VIEW_REPORT)


def test_administrator_empty_list(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    response = client.get("/reports/")
    assert response.status_code == 200
    assert b"No reports have been generated yet." in response.content
    assert b"Generate PDF" in response.content
    assert b"Reports" in response.content


def test_invalid_period_returns_400(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    response = client.post(
        "/reports/create/",
        {"period_start": "2026-11-15", "period_end": "2026-11-01"},
    )
    assert response.status_code == 400
    assert b"Start date must be on or before the end date." in response.content
    assert Report.objects.count() == 0


def test_period_over_31_days_returns_400(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    response = client.post(
        "/reports/create/",
        {"period_start": "2026-01-01", "period_end": "2026-02-01"},
    )
    assert response.status_code == 400
    assert b"Monthly reports cannot exceed 31 days." in response.content
    assert Report.objects.count() == 0


def test_csrf_required_to_create_report(administrator: User) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(administrator)
    response = client.post(
        "/reports/create/",
        {"period_start": "2026-11-01", "period_end": "2026-11-15"},
    )
    assert response.status_code == 403
    assert Report.objects.count() == 0


def test_administrator_generates_and_downloads_pdf(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    response = client.post(
        "/reports/create/",
        {"period_start": "2026-11-01", "period_end": "2026-11-15"},
    )
    assert response.status_code == 302
    report = Report.objects.get()
    assert report.status == Report.Status.SUCCESS
    assert redirect_location(response) == f"/reports/{report.pk}/"
    detail = client.get(f"/reports/{report.pk}/")
    assert detail.status_code == 200
    assert b"Download PDF" in detail.content
    download = client.get(f"/reports/{report.pk}/download/")
    assert download.status_code == 200
    assert download["Content-Type"].startswith("application/pdf")
    payload = b"".join(download.streaming_content)  # type: ignore[attr-defined]
    assert payload.startswith(b"%PDF-")
    assert "railops-monthly-2026-11-01-to-2026-11-15.pdf" in download["Content-Disposition"]
    listing = client.get("/reports/")
    assert b"2026-11-01" in listing.content


def test_missing_report_is_404(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    missing = uuid4()
    assert client.get(f"/reports/{missing}/").status_code == 404
    assert client.get(f"/reports/{missing}/download/").status_code == 404


def test_pending_report_cannot_be_downloaded(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    report = Report.objects.create(
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
        requested_by=administrator,
        status=Report.Status.PENDING,
    )
    response = client.get(f"/reports/{report.pk}/download/")
    assert response.status_code == 302
    assert redirect_location(response) == f"/reports/{report.pk}/"


def test_create_get_is_not_allowed(client: Client, administrator: User) -> None:
    client.force_login(administrator)
    assert client.get("/reports/create/").status_code == 405


def test_viewer_cannot_download_existing_report(
    client: Client,
    administrator: User,
    viewer: User,
) -> None:
    report = Report.objects.create(
        period_start=date(2026, 11, 1),
        period_end=date(2026, 11, 15),
        requested_by=administrator,
        status=Report.Status.SUCCESS,
    )
    client.force_login(viewer)
    assert client.get(f"/reports/{report.pk}/").status_code == 403
    assert client.get(f"/reports/{report.pk}/download/").status_code == 403
