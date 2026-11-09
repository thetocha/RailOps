"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractUser


@pytest.fixture
def user(django_user_model: type[AbstractUser]) -> AbstractUser:
    return django_user_model.objects.create_user(
        username="operator",
        email="operator@example.com",
        password="a-strong-test-password-123",
    )
