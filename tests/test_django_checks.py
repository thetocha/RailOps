from __future__ import annotations

from io import StringIO

from django.core.management import call_command


def test_django_system_checks_pass() -> None:
    output = StringIO()
    call_command("check", stdout=output, stderr=output)
    combined = output.getvalue()
    assert "SystemCheckError" not in combined
