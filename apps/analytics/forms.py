"""HTML date-range form for analytics. GET only."""

from __future__ import annotations

from datetime import date
from typing import Any

from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.accounts.forms import apply_bootstrap
from apps.analytics.periods import (
    DEFAULT_REPORTING_DAYS,
    MAX_REPORTING_DAYS,
    default_reporting_period,
    validate_reporting_period,
)


class AnalyticsPeriodForm(forms.Form):
    period_start = forms.DateField(
        label="Period start",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    period_end = forms.DateField(
        label="Period end",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            start, end = default_reporting_period()
            self.fields["period_start"].initial = start
            self.fields["period_end"].initial = end
        apply_bootstrap(self)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        start = cleaned.get("period_start")
        end = cleaned.get("period_end")
        if isinstance(start, date) and isinstance(end, date):
            try:
                validate_reporting_period(start=start, end=end)
            except DjangoValidationError as exc:
                message_dict = getattr(exc, "message_dict", None)
                if isinstance(message_dict, dict):
                    for field, messages in message_dict.items():
                        target = field if field in self.fields else None
                        for message in messages:
                            self.add_error(target, message)
                else:
                    self.add_error(None, exc)
        return cleaned

    @property
    def max_days(self) -> int:
        return MAX_REPORTING_DAYS

    @property
    def default_days(self) -> int:
        return DEFAULT_REPORTING_DAYS
