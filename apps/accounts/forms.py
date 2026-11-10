"""HTML forms for authentication and user management."""

from __future__ import annotations

import logging
from typing import Any, cast

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.models import Group

from apps.accounts.models import User
from apps.accounts.permissions import ROLE_GROUP_NAMES, role_group_queryset

logger = logging.getLogger("django.security")

_CONTROL = "form-control"
_SELECT = "form-select"
_CHECK = "form-check-input"


def _validated_unique_email(email: str, *, exclude_pk: int | None) -> str:
    cleaned = email.strip()
    if not cleaned:
        raise forms.ValidationError("Email is required.")
    query = User.objects.filter(email=cleaned)
    if exclude_pk is not None:
        query = query.exclude(pk=exclude_pk)
    if query.exists():
        raise forms.ValidationError("A user with that email address already exists.")
    return cleaned


def _apply_bootstrap(form: forms.BaseForm) -> None:
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", _CHECK)
        elif isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
            # Option inputs inherit this class. The default wrapper <div> also
            # receives it; form_field.html renders options individually so the
            # wrapper is not sized as a 1em Bootstrap checkbox.
            widget.attrs.setdefault("class", _CHECK)
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs.setdefault("class", _SELECT)
        else:
            css = widget.attrs.get("class", "")
            if _CONTROL not in css.split():
                widget.attrs["class"] = f"{css} {_CONTROL}".strip()


class RailOpsAuthenticationForm(AuthenticationForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.setdefault("autocomplete", "username")
        self.fields["password"].widget.attrs.setdefault("autocomplete", "current-password")
        _apply_bootstrap(self)

    def get_invalid_login_error(self) -> forms.ValidationError:
        username = self.data.get("username", "")
        logger.info("Failed login attempt username=%s", username)
        return super().get_invalid_login_error()


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class StyledSetPasswordForm(SetPasswordForm):  # type: ignore[type-arg]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class UserCreateForm(forms.ModelForm):  # type: ignore[type-arg]
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Assign at least one role. Access is granted by group permissions.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        groups_field = cast(forms.ModelMultipleChoiceField, self.fields["groups"])  # type: ignore[type-arg]
        groups_field.queryset = role_group_queryset()
        self.fields["email"].required = True
        self.fields["is_active"].initial = True
        _apply_bootstrap(self)

    def clean_email(self) -> str:
        return _validated_unique_email(self.cleaned_data.get("email") or "", exclude_pk=None)

    def clean_groups(self) -> list[Group]:
        groups = list(self.cleaned_data["groups"])
        allowed = set(ROLE_GROUP_NAMES)
        invalid = [group.name for group in groups if group.name not in allowed]
        if invalid:
            raise forms.ValidationError("Only the standard role groups can be assigned.")
        return groups

    def clean_password2(self) -> str:
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn’t match.")
        return password2 or ""

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        password = cleaned.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error("password2", error)
        return cleaned


class UserUpdateForm(forms.ModelForm):  # type: ignore[type-arg]
    password1 = forms.CharField(
        label="New password",
        strip=False,
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Leave blank to keep the current password. The stored hash is never shown.",
    )
    password2 = forms.CharField(
        label="Confirm new password",
        strip=False,
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Assign at least one role.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        groups_field = cast(forms.ModelMultipleChoiceField, self.fields["groups"])  # type: ignore[type-arg]
        groups_field.queryset = role_group_queryset()
        self.fields["email"].required = True
        if self.instance.pk:
            groups_field.initial = self.instance.groups.filter(name__in=ROLE_GROUP_NAMES)
        _apply_bootstrap(self)

    def clean_email(self) -> str:
        return _validated_unique_email(
            self.cleaned_data.get("email") or "",
            exclude_pk=self.instance.pk,
        )

    def clean_groups(self) -> list[Group]:
        groups = list(self.cleaned_data["groups"])
        allowed = set(ROLE_GROUP_NAMES)
        invalid = [group.name for group in groups if group.name not in allowed]
        if invalid:
            raise forms.ValidationError("Only the standard role groups can be assigned.")
        return groups

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        password1 = cleaned.get("password1") or ""
        password2 = cleaned.get("password2") or ""
        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "The two password fields didn’t match.")
            elif password1:
                try:
                    password_validation.validate_password(password1, self.instance)
                except forms.ValidationError as error:
                    self.add_error("password2", error)
        return cleaned
