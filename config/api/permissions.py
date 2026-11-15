"""DRF permissions that delegate to Django model permissions."""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


def require_django_perm(perm: str) -> type[BasePermission]:
    class _DjangoPermission(BasePermission):
        def has_permission(self, request: Request, view: APIView) -> bool:
            user = request.user
            return bool(user and user.is_authenticated and user.has_perm(perm))

    return _DjangoPermission
