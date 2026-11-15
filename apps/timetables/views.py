"""HTTP adapters for train services. Writes happen through the integration sync."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from apps.accounts.http import remaining_querystring
from apps.infrastructure.models import Station
from apps.timetables.models import TrainService
from apps.timetables.permissions import ViewTrainServiceRequiredMixin
from apps.timetables.selectors import stops_for_service, train_service_directory

ITEMS_PER_PAGE = 20


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _parse_uuid(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


class TrainServiceListView(ViewTrainServiceRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        service_date = _parse_date(request.GET.get("date"))
        station_id = _parse_uuid(request.GET.get("station"))
        train_number = request.GET.get("q", "")
        paginator = Paginator(
            train_service_directory(
                service_date=service_date,
                station_id=station_id,
                train_number=train_number,
            ),
            ITEMS_PER_PAGE,
        )
        page = paginator.get_page(request.GET.get("page"))
        return render(
            request,
            "timetables/service_list.html",
            {
                "page": page,
                "service_date": service_date.isoformat() if service_date else "",
                "station_id": str(station_id) if station_id else "",
                "search": train_number,
                "stations": Station.objects.order_by("name"),
                "querystring": remaining_querystring(request),
            },
        )


class TrainServiceDetailView(ViewTrainServiceRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        service = get_object_or_404(
            TrainService.objects.select_related("origin", "destination"),
            pk=pk,
        )
        return render(
            request,
            "timetables/service_detail.html",
            {"service": service, "stops": stops_for_service(service)},
        )
