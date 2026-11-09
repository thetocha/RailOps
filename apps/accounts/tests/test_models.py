from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, transaction
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_auth_user_model_is_accounts_user() -> None:
    user_model = get_user_model()
    assert user_model._meta.app_label == "accounts"
    assert user_model.__name__ == "User"


def test_create_user_sets_active_flag_and_timestamps() -> None:
    user_model = get_user_model()
    before = timezone.now()
    user = user_model.objects.create_user(
        username="anna",
        email="anna@example.com",
        password="a-strong-test-password-123",
    )
    assert user.pk is not None
    assert user.is_active is True
    assert user.created_at >= before
    assert user.updated_at >= before
    assert user.check_password("a-strong-test-password-123")
    assert user.password != "a-strong-test-password-123"  # noqa: S105
    identify_hasher(user.password)


def test_user_str_is_username() -> None:
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="dispatcher1",
        password="a-strong-test-password-123",
    )
    assert str(user) == "dispatcher1"


def test_duplicate_email_is_rejected_by_unique_constraint() -> None:
    user_model = get_user_model()
    user_model.objects.create_user(
        username="mail-one",
        email="shared@example.com",
        password="a-strong-test-password-123",
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        user_model.objects.create_user(
            username="mail-two",
            email="shared@example.com",
            password="a-strong-test-password-123",
        )


def test_blank_emails_are_allowed_more_than_once() -> None:
    user_model = get_user_model()
    first = user_model.objects.create_user(
        username="blank-one",
        email="",
        password="a-strong-test-password-123",
    )
    second = user_model.objects.create_user(
        username="blank-two",
        email="",
        password="a-strong-test-password-123",
    )
    assert first.email == ""
    assert second.email == ""
    assert first.pk != second.pk


def test_is_active_is_inherited_not_redeclared() -> None:
    source = Path(__file__).resolve().parents[1] / "models.py"
    text = source.read_text(encoding="utf-8")
    assert "is_active =" not in text
    user_model = get_user_model()
    assert issubclass(user_model, AbstractUser)
    assert user_model._meta.get_field("is_active").name == "is_active"
