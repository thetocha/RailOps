"""Session safety for deactivated accounts.

Django's ModelBackend already treats inactive users as unauthenticated. This
middleware is defense in depth for backends that still return an inactive user.
"""

from collections.abc import Callable
from typing import Any

from django.contrib.auth import logout
from django.contrib.auth.middleware import LoginRequiredMiddleware as DjangoLoginRequiredMiddleware
from django.http import HttpRequest, HttpResponse, HttpResponseBase


class ActiveUserSessionMiddleware:
    """Log out authenticated users whose ``is_active`` flag is false."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and not user.is_active:
            logout(request)
        return self.get_response(request)


class LoginRequiredMiddleware(DjangoLoginRequiredMiddleware):
    """HTML views require a session. ``/api/`` is authenticated by DRF instead."""

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., Any],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponseBase | None:
        if request.path.startswith("/api/"):
            return None
        return super().process_view(request, view_func, view_args, view_kwargs)
