"""Session safety for deactivated accounts.

Django's ModelBackend already treats inactive users as unauthenticated. This
middleware is defense in depth for backends that still return an inactive user.
"""

from collections.abc import Callable

from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse


class ActiveUserSessionMiddleware:
    """Log out authenticated users whose ``is_active`` flag is false."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and not user.is_active:
            logout(request)
        return self.get_response(request)
