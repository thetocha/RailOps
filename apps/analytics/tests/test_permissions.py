from __future__ import annotations

import pytest
from django.contrib.auth.models import Group

from apps.accounts.models import User
from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER
from apps.analytics.permissions import can_view_analytics, ensure_analytics_permissions

pytestmark = pytest.mark.django_db


def test_all_roles_can_view_analytics(
    administrator: User,
    dispatcher: User,
    viewer: User,
) -> None:
    assert can_view_analytics(administrator)
    assert can_view_analytics(dispatcher)
    assert can_view_analytics(viewer)


def test_ensure_analytics_permissions_is_idempotent(role_groups: dict[str, Group]) -> None:
    ensure_analytics_permissions()
    ensure_analytics_permissions()
    viewer = role_groups[GROUP_VIEWER]
    admin = role_groups[GROUP_ADMINISTRATOR]
    dispatcher = role_groups[GROUP_DISPATCHER]
    assert viewer.permissions.filter(codename="view_operationalanalytics").exists()
    assert admin.permissions.filter(codename="view_operationalanalytics").exists()
    assert dispatcher.permissions.filter(codename="view_operationalanalytics").exists()
