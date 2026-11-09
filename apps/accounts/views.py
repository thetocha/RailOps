"""HTTP adapters for authentication and user management. Business writes go through services."""

from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView

from apps.accounts.forms import (
    RailOpsAuthenticationForm,
    StyledPasswordChangeForm,
    StyledPasswordResetForm,
    StyledSetPasswordForm,
    UserCreateForm,
    UserUpdateForm,
)
from apps.accounts.models import User
from apps.accounts.permissions import (
    DashboardAccessMixin,
    ManageUsersRequiredMixin,
    require_authenticated_user,
)
from apps.accounts.selectors import user_directory
from apps.accounts.services import create_user, deactivate_user, update_user

USERS_PER_PAGE = 20


class RailOpsLoginView(LoginView):
    authentication_form = RailOpsAuthenticationForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class RailOpsLogoutView(LogoutView):
    next_page = "login"


class RailOpsPasswordChangeView(PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")


class RailOpsPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"


class RailOpsPasswordResetView(PasswordResetView):
    form_class = StyledPasswordResetForm
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class RailOpsPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class RailOpsPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = StyledSetPasswordForm
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class RailOpsPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


class DashboardView(DashboardAccessMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = require_authenticated_user(self.request.user)
        context["role_names"] = list(user.groups.order_by("name").values_list("name", flat=True))
        return context


class UserListView(ManageUsersRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        search = request.GET.get("q", "")
        paginator = Paginator(user_directory(search=search), USERS_PER_PAGE)
        page = paginator.get_page(request.GET.get("page"))
        return render(
            request,
            "accounts/user_list.html",
            {"page": page, "search": search},
        )


@method_decorator(sensitive_post_parameters("password1", "password2"), name="dispatch")
class UserCreateView(ManageUsersRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "accounts/user_form.html",
            {"form": UserCreateForm(), "title": "Create user"},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = UserCreateForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "accounts/user_form.html",
                {"form": form, "title": "Create user"},
            )
        actor = require_authenticated_user(request.user)
        create_user(
            actor=actor,
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data.get("first_name", ""),
            last_name=form.cleaned_data.get("last_name", ""),
            is_active=form.cleaned_data.get("is_active", True),
            groups=form.cleaned_data["groups"],
        )
        messages.success(request, "User created.")
        return redirect("user_list")


@method_decorator(sensitive_post_parameters("password1", "password2"), name="dispatch")
class UserUpdateView(ManageUsersRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        target = get_object_or_404(User, pk=pk)
        form = UserUpdateForm(instance=target)
        return render(
            request,
            "accounts/user_form.html",
            {"form": form, "title": f"Edit {target.username}", "target_user": target},
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        target = get_object_or_404(User, pk=pk)
        form = UserUpdateForm(request.POST, instance=target)
        if not form.is_valid():
            return render(
                request,
                "accounts/user_form.html",
                {"form": form, "title": f"Edit {target.username}", "target_user": target},
            )
        actor = require_authenticated_user(request.user)
        password = form.cleaned_data.get("password1") or None
        try:
            update_user(
                actor=actor,
                user=target,
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
                is_active=form.cleaned_data.get("is_active", True),
                groups=form.cleaned_data["groups"],
                password=password,
            )
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
            return render(
                request,
                "accounts/user_form.html",
                {"form": form, "title": f"Edit {target.username}", "target_user": target},
            )
        messages.success(request, "User updated.")
        return redirect("user_list")


class UserDeactivateView(ManageUsersRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        target = get_object_or_404(User, pk=pk)
        return render(
            request,
            "accounts/user_confirm_deactivate.html",
            {"target_user": target},
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        target = get_object_or_404(User, pk=pk)
        actor = require_authenticated_user(request.user)
        try:
            deactivate_user(actor=actor, user=target)
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
            return redirect("user_list")
        messages.success(request, f"User {target.username} deactivated.")
        return redirect("user_list")
