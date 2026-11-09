"""User-management write operations. Views must not duplicate this logic."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.accounts.permissions import can_manage_users, require_authenticated_user

logger = logging.getLogger(__name__)


def sync_staff_flag(user: User) -> User:
    """Grant Django admin access when the user can manage users (or is a superuser)."""
    if user.is_superuser:
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])
        return user
    should_be_staff = user.groups.filter(
        permissions__content_type__app_label="accounts",
        permissions__codename="manage_users",
    ).exists()
    if user.is_staff != should_be_staff:
        user.is_staff = should_be_staff
        user.save(update_fields=["is_staff"])
    return user


def _assert_can_manage(*, actor: User) -> None:
    if not can_manage_users(actor):
        raise PermissionDenied


def _groups_grant_manage_users(groups: Iterable[Group]) -> bool:
    group_ids = [group.pk for group in groups if group.pk is not None]
    if not group_ids:
        return False
    return Group.objects.filter(
        pk__in=group_ids,
        permissions__content_type__app_label="accounts",
        permissions__codename="manage_users",
    ).exists()


def _assert_password_is_hashed(user: User) -> None:
    identify_hasher(user.password)


@transaction.atomic
def create_user(
    *,
    actor: User,
    username: str,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    is_active: bool = True,
    groups: Iterable[Group],
) -> User:
    actor = require_authenticated_user(actor)
    _assert_can_manage(actor=actor)
    group_list = list(groups)
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
    )
    _assert_password_is_hashed(user)
    user.groups.set(group_list)
    sync_staff_flag(user)
    logger.info("Created user username=%s actor=%s", user.username, actor.username)
    return user


@transaction.atomic
def update_user(
    *,
    actor: User,
    user: User,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    is_active: bool,
    groups: Iterable[Group],
    password: str | None = None,
) -> User:
    actor = require_authenticated_user(actor)
    _assert_can_manage(actor=actor)
    group_list = list(groups)

    if actor.pk == user.pk and not actor.is_superuser:
        if not _groups_grant_manage_users(group_list):
            raise ValidationError("You cannot remove your own user-management permission.")
        if not is_active:
            raise ValidationError("You cannot deactivate your own account.")

    user.username = username
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = is_active
    if password:
        user.set_password(password)
    user.save()
    if password:
        _assert_password_is_hashed(user)
    user.groups.set(group_list)
    sync_staff_flag(user)
    logger.info("Updated user username=%s actor=%s", user.username, actor.username)
    return user


@transaction.atomic
def deactivate_user(*, actor: User, user: User) -> User:
    actor = require_authenticated_user(actor)
    _assert_can_manage(actor=actor)
    if actor.pk == user.pk:
        raise ValidationError("You cannot deactivate your own account.")
    if not user.is_active:
        return user
    user.is_active = False
    user.save(update_fields=["is_active", "updated_at"])
    logger.info("Deactivated user username=%s actor=%s", user.username, actor.username)
    return user
