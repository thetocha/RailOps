"""User-management write operations. Views must not duplicate this logic."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.accounts.permissions import can_manage_users, require_authenticated_user

logger = logging.getLogger(__name__)

_DB_SESSION_ENGINES = frozenset(
    {
        "django.contrib.sessions.backends.db",
        "django.contrib.sessions.backends.cached_db",
    }
)


def sync_staff_flag(user: User) -> User:
    """Django admin is reserved for superusers.

    Role-based Administrators use the application Users UI. ``is_staff`` is
    cleared for anyone who is not a superuser so ``/admin/`` is not a
    privilege-escalation path.
    """
    should_be_staff = user.is_superuser
    if user.is_staff != should_be_staff:
        user.is_staff = should_be_staff
        user.save(update_fields=["is_staff"])
    return user


def invalidate_user_sessions(user: User) -> None:
    """Delete persisted sessions for ``user`` so deactivation takes effect immediately."""
    if settings.SESSION_ENGINE not in _DB_SESSION_ENGINES:
        logger.warning(
            "Cannot enumerate sessions for engine=%s; relying on ActiveUserSessionMiddleware",
            settings.SESSION_ENGINE,
        )
        return

    from django.contrib.sessions.models import Session

    user_id = str(user.pk)
    stale_keys: list[str] = []
    for session in Session.objects.iterator():
        data = session.get_decoded()
        session_key = session.session_key
        if session_key is not None and str(data.get(SESSION_KEY, "")) == user_id:
            stale_keys.append(session_key)
    if stale_keys:
        Session.objects.filter(session_key__in=stale_keys).delete()
        logger.info(
            "Invalidated %s session(s) for username=%s",
            len(stale_keys),
            user.username,
        )


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
    became_inactive = user.is_active and not is_active

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
    if became_inactive:
        invalidate_user_sessions(user)
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
    invalidate_user_sessions(user)
    logger.info("Deactivated user username=%s actor=%s", user.username, actor.username)
    return user
