"""Forms for administrator-triggered timetable import."""

from __future__ import annotations

from typing import Any

from django import forms

from apps.accounts.forms import apply_bootstrap

MAX_CSV_BYTES = 1_000_000


class TimetableSyncForm(forms.Form):
    provider = forms.ChoiceField(
        choices=(
            ("mock", "Mock provider"),
            ("csv", "CSV file"),
        )
    )
    csv_file = forms.FileField(
        required=False,
        help_text="Required when provider is CSV. UTF-8, max 1 MB.",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        apply_bootstrap(self)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        if cleaned.get("provider") == "csv" and not cleaned.get("csv_file"):
            self.add_error("csv_file", "Choose a CSV file.")
        return cleaned

    def clean_csv_file(self) -> Any:
        uploaded = self.cleaned_data.get("csv_file")
        if uploaded is None:
            return None
        if uploaded.size > MAX_CSV_BYTES:
            raise forms.ValidationError("CSV file is larger than 1 MB.")
        name = getattr(uploaded, "name", "") or ""
        if not name.lower().endswith(".csv"):
            raise forms.ValidationError("Upload a .csv file.")
        return uploaded
