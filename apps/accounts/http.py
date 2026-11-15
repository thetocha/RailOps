"""Small HTTP helpers shared by HTML list pages."""

from __future__ import annotations

from django.http import HttpRequest


def remaining_querystring(request: HttpRequest) -> str:
    """GET query string without ``page``, ready to prefix pagination links."""
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return f"{encoded}&" if encoded else ""
