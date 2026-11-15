from __future__ import annotations

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission

from apps.accounts.models import User
from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER
from apps.reports.permissions import (
    can_add_reports,
    can_view_reports,
    ensure_report_permissions,
)

pytestmark = pytest.mark.django_db


def test_only_administrator_receives_report_permissions(role_groups: dict[str, Group]) -> None:
    administrator = role_groups[GROUP_ADMINISTRATOR]
    dispatcher = role_groups[GROUP_DISPATCHER]
    viewer = role_groups[GROUP_VIEWER]
    assert administrator.permissions.filter(codename="view_report").exists()
    assert administrator.permissions.filter(codename="add_report").exists()
    assert not administrator.permissions.filter(codename="change_report").exists()
    assert not administrator.permissions.filter(codename="delete_report").exists()
    assert not dispatcher.permissions.filter(codename="view_report").exists()
    assert not dispatcher.permissions.filter(codename="add_report").exists()
    assert not viewer.permissions.filter(codename="view_report").exists()
    assert not viewer.permissions.filter(codename="add_report").exists()


def test_ensure_report_permissions_revokes_stale(role_groups: dict[str, Group]) -> None:
    dispatcher = role_groups[GROUP_DISPATCHER]
    change_report = Permission.objects.get(
        content_type__app_label="reports",
        codename="change_report",
    )
    dispatcher.permissions.add(change_report)
    ensure_report_permissions()
    ensure_report_permissions()
    assert not dispatcher.permissions.filter(pk=change_report.pk).exists()


def test_helpers_follow_permissions(
    administrator: User,
    dispatcher: User,
    viewer: User,
) -> None:
    assert can_view_reports(administrator)
    assert can_add_reports(administrator)
    assert not can_view_reports(dispatcher)
    assert not can_add_reports(dispatcher)
    assert not can_view_reports(viewer)
    assert not can_add_reports(viewer)
    assert not can_view_reports(AnonymousUser())
    assert not can_add_reports(object())
