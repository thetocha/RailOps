"""Map Django exceptions to JSON bodies without stack traces or internals."""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _validation_body(exc: DjangoValidationError) -> dict[str, Any]:
    if hasattr(exc, "message_dict") and exc.message_dict:
        return dict(exc.message_dict)
    messages = list(getattr(exc, "messages", [str(exc)]))
    if len(messages) == 1:
        return {"detail": messages[0]}
    return {"detail": messages}


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, DjangoPermissionDenied):
        return Response(
            {"detail": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if isinstance(exc, DjangoValidationError):
        return Response(_validation_body(exc), status=status.HTTP_400_BAD_REQUEST)

    response = exception_handler(exc, context)
    if response is not None:
        return response

    logger.exception("Unhandled API exception")
    return Response(
        {"detail": "A server error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
