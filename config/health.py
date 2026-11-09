"""Public liveness endpoint. Uses a cheap SELECT 1 — not a metrics query."""

from __future__ import annotations

import logging

from django.contrib.auth.decorators import login_not_required
from django.db import connection
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)


@login_not_required
def health(_request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.error("Health check database query failed")
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
