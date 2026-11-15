"""HTTP adapters for analytics. Calculations live in services and metrics."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from apps.analytics.forms import AnalyticsPeriodForm
from apps.analytics.permissions import ViewAnalyticsRequiredMixin
from apps.analytics.schemas import OverviewMetrics
from apps.analytics.services import build_overview
from apps.timetables.models import ON_TIME_THRESHOLD_SECONDS


class AnalyticsOverviewView(ViewAnalyticsRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        form = AnalyticsPeriodForm(request.GET) if request.GET else AnalyticsPeriodForm()
        overview: OverviewMetrics | None = None
        if form.is_valid():
            overview = build_overview(
                period_start=form.cleaned_data["period_start"],
                period_end=form.cleaned_data["period_end"],
            )
        elif not form.is_bound:
            overview = build_overview()
        return render(
            request,
            "analytics/overview.html",
            {
                "form": form,
                "overview": overview,
                "on_time_threshold_seconds": ON_TIME_THRESHOLD_SECONDS,
            },
        )
