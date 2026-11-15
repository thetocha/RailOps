from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from django.contrib.auth.models import Group, Permission
from django.forms import ModelChoiceField
from django.test import Client

from apps.accounts.models import User
from apps.accounts.permissions import GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER
from apps.incidents.permissions import (
    can_manage_incidents,
    can_reopen_closed_incident,
    can_view_incidents,
    ensure_incident_permissions,
)

pytestmark = pytest.mark.django_db


def test_role_groups_receive_incident_permissions(role_groups: dict[str, Group]) -> None:
    administrator = role_groups[GROUP_ADMINISTRATOR]
    dispatcher = role_groups[GROUP_DISPATCHER]
    viewer = role_groups[GROUP_VIEWER]
    assert administrator.permissions.filter(codename="reopen_closed_incident").exists()
    assert administrator.permissions.filter(codename="add_incident").exists()
    assert not administrator.permissions.filter(codename="delete_incident").exists()
    assert dispatcher.permissions.filter(codename="change_incident").exists()
    assert not dispatcher.permissions.filter(codename="reopen_closed_incident").exists()
    assert viewer.permissions.filter(codename="view_incident").exists()
    assert not viewer.permissions.filter(codename="add_incident").exists()
    assert viewer.permissions.filter(codename="view_incidentevent").exists()
    assert not viewer.permissions.filter(codename="change_incidentevent").exists()


def test_ensure_incident_permissions_revokes_stale(role_groups: dict[str, Group]) -> None:
    viewer = role_groups[GROUP_VIEWER]
    add_incident = Permission.objects.get(
        content_type__app_label="incidents",
        codename="add_incident",
    )
    viewer.permissions.add(add_incident)
    ensure_incident_permissions()
    assert not viewer.permissions.filter(pk=add_incident.pk).exists()


def test_helpers_follow_permissions(
    administrator: User,
    dispatcher: User,
    viewer: User,
) -> None:
    assert can_manage_incidents(administrator)
    assert can_reopen_closed_incident(administrator)
    assert can_manage_incidents(dispatcher)
    assert not can_reopen_closed_incident(dispatcher)
    assert can_view_incidents(viewer)
    assert not can_manage_incidents(viewer)


def test_views_do_not_hardcode_role_group_names() -> None:
    source = Path(__file__).resolve().parents[1] / "views.py"
    text = source.read_text(encoding="utf-8")
    for role_name in (GROUP_ADMINISTRATOR, GROUP_DISPATCHER, GROUP_VIEWER):
        assert role_name not in text


def test_assign_form_includes_inactive_current_assignee(
    administrator: User,
) -> None:
    from apps.incidents.forms import IncidentAssignForm

    administrator.is_active = False
    administrator.save(update_fields=["is_active"])
    form = IncidentAssignForm(current_assignee=administrator)
    assigned_field = cast("ModelChoiceField[User]", form.fields["assigned_to"])
    queryset = assigned_field.queryset
    assert queryset is not None
    pks = set(queryset.values_list("pk", flat=True))
    assert administrator.pk in pks


def test_incident_admin_is_read_only() -> None:
    from django.contrib.admin.sites import AdminSite
    from django.test import RequestFactory

    from apps.incidents.admin import IncidentAdmin
    from apps.incidents.models import Incident

    superuser = User.objects.create_superuser(
        username="root",
        email="root@example.com",
        password="a-strong-test-password-123",
    )
    request = RequestFactory().get("/admin/incidents/incident/")
    request.user = superuser
    model_admin = IncidentAdmin(Incident, AdminSite())
    assert model_admin.has_view_permission(request) is True
    assert model_admin.has_add_permission(request) is False
    assert model_admin.has_change_permission(request) is False
    assert model_admin.has_delete_permission(request) is False


def test_direct_add_incident_permission_opens_create(
    client: Client,
    viewer: User,
    add_incident_permission: Permission,
) -> None:
    viewer.user_permissions.add(add_incident_permission)
    client.force_login(viewer)
    assert client.get("/incidents/create/").status_code == 200
