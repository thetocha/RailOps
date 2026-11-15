"""HTTP adapters for reports. PDF bytes are produced in services."""

from __future__ import annotations

from uuid import UUID

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.http import remaining_querystring
from apps.accounts.permissions import require_authenticated_user
from apps.reports.forms import MonthlyReportForm
from apps.reports.models import Report
from apps.reports.permissions import AddReportRequiredMixin, ViewReportRequiredMixin
from apps.reports.selectors import report_directory
from apps.reports.services import generate_monthly_operations_report, get_downloadable_report

ITEMS_PER_PAGE = 20


class ReportListView(ViewReportRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        paginator = Paginator(report_directory(), ITEMS_PER_PAGE)
        page = paginator.get_page(request.GET.get("page"))
        return render(
            request,
            "reports/report_list.html",
            {
                "page": page,
                "form": MonthlyReportForm(),
                "querystring": remaining_querystring(request),
            },
        )


class ReportCreateView(AddReportRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = MonthlyReportForm(request.POST)
        if not form.is_valid():
            paginator = Paginator(report_directory(), ITEMS_PER_PAGE)
            page = paginator.get_page(request.GET.get("page"))
            return render(
                request,
                "reports/report_list.html",
                {
                    "page": page,
                    "form": form,
                    "querystring": remaining_querystring(request),
                },
                status=400,
            )
        report = generate_monthly_operations_report(
            actor=require_authenticated_user(request.user),
            period_start=form.cleaned_data["period_start"],
            period_end=form.cleaned_data["period_end"],
        )
        if report.status == Report.Status.SUCCESS:
            messages.success(request, "Monthly operations report generated.")
        else:
            messages.error(request, "The report could not be generated.")
        return redirect("report_detail", pk=report.pk)


class ReportDetailView(ViewReportRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        report = get_object_or_404(Report.objects.select_related("requested_by"), pk=pk)
        return render(request, "reports/report_detail.html", {"report": report})


class ReportDownloadView(ViewReportRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> FileResponse | HttpResponse:
        get_object_or_404(Report, pk=pk)
        try:
            report = get_downloadable_report(
                actor=require_authenticated_user(request.user),
                report_id=pk,
            )
        except ValidationError as error:
            messages.error(
                request, error.messages[0] if error.messages else "Download unavailable."
            )
            return redirect("report_detail", pk=pk)
        filename = f"railops-monthly-{report.period_start}-to-{report.period_end}.pdf"
        return FileResponse(
            report.file.open("rb"),
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )
