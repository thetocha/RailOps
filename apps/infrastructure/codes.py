"""Shared infrastructure code normalisation."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError

CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,31}$")


def normalize_infrastructure_code(raw: str) -> str:
    """Strip, uppercase, and validate a station or line code."""
    code = raw.strip().upper()
    if not CODE_PATTERN.fullmatch(code):
        raise ValidationError(
            "Code must start with a letter or digit and may contain letters, "
            "digits, underscores, and hyphens (max 32 characters)."
        )
    return code
