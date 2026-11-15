"""HTML adapters for sync runs. Persistence goes through synchronize_timetables."""

from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from apps.accounts.http import remaining_querystring
from apps.accounts.permissions import require_authenticated_user
from apps.integrations.forms import TimetableSyncForm
from apps.integrations.models import ExternalSyncRun
from apps.integrations.permissions import RunSyncRequiredMixin, ViewSyncRunRequiredMixin
from apps.integrations.services import build_provider, synchronize_timetables

ITEMS_PER_PAGE = 20


class SyncRunListView(ViewSyncRunRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        paginator = Paginator(ExternalSyncRun.objects.all(), ITEMS_PER_PAGE)
        page = paginator.get_page(request.GET.get("page"))
        return render(
            request,
            "integrations/sync_run_list.html",
            {
                "page": page,
                "form": TimetableSyncForm(),
                "querystring": remaining_querystring(request),
            },
        )


class TimetableSyncView(RunSyncRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = TimetableSyncForm(request.POST, request.FILES)
        if not form.is_valid():
            paginator = Paginator(ExternalSyncRun.objects.all(), ITEMS_PER_PAGE)
            page = paginator.get_page(request.GET.get("page"))
            return render(
                request,
                "integrations/sync_run_list.html",
                {"page": page, "form": form, "querystring": remaining_querystring(request)},
            )
        actor = require_authenticated_user(request.user)
        csv_content: str | None = None
        uploaded = form.cleaned_data.get("csv_file")
        if uploaded is not None:
            csv_content = uploaded.read().decode("utf-8")
        try:
            provider = build_provider(
                name=form.cleaned_data["provider"],
                csv_content=csv_content,
            )
            run = synchronize_timetables(actor=actor, provider=provider)
        except (ValidationError, UnicodeDecodeError, ValueError) as error:
            messages.error(request, str(error))
            return redirect("sync_run_list")
        if run.status == ExternalSyncRun.Status.SUCCESS:
            messages.success(request, "Timetable synchronization completed.")
        elif run.status == ExternalSyncRun.Status.PARTIAL:
            messages.warning(request, "Synchronization completed with some rejected records.")
        else:
            messages.error(request, "Synchronization failed. See the error summary.")
        return redirect("sync_run_list")
