"""HTTP adapters for stations and railway lines. Writes go through services."""

from __future__ import annotations

from uuid import UUID

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.http import remaining_querystring
from apps.accounts.permissions import require_authenticated_user
from apps.infrastructure.forms import RailwayLineForm, StationForm
from apps.infrastructure.models import RailwayLine, Station
from apps.infrastructure.permissions import (
    AddRailwayLineRequiredMixin,
    AddStationRequiredMixin,
    ChangeRailwayLineRequiredMixin,
    ChangeStationRequiredMixin,
    ViewRailwayLineRequiredMixin,
    ViewStationRequiredMixin,
)
from apps.infrastructure.selectors import (
    lines_for_station,
    parse_active_filter,
    railway_line_directory,
    station_directory,
)
from apps.infrastructure.services import (
    create_railway_line,
    create_station,
    deactivate_railway_line,
    deactivate_station,
    update_railway_line,
    update_station,
)

ITEMS_PER_PAGE = 20


def _station_list_context(request: HttpRequest) -> dict[str, object]:
    search = request.GET.get("q", "")
    status = request.GET.get("status", "active")
    is_active = parse_active_filter(status)
    paginator = Paginator(
        station_directory(search=search, is_active=is_active),
        ITEMS_PER_PAGE,
    )
    page = paginator.get_page(request.GET.get("page"))
    return {
        "page": page,
        "search": search,
        "status": status if status in {"active", "inactive", "all"} else "active",
        "querystring": remaining_querystring(request),
    }


def _line_list_context(request: HttpRequest) -> dict[str, object]:
    search = request.GET.get("q", "")
    status = request.GET.get("status", "active")
    is_active = parse_active_filter(status)
    paginator = Paginator(
        railway_line_directory(search=search, is_active=is_active),
        ITEMS_PER_PAGE,
    )
    page = paginator.get_page(request.GET.get("page"))
    return {
        "page": page,
        "search": search,
        "status": status if status in {"active", "inactive", "all"} else "active",
        "querystring": remaining_querystring(request),
    }


def _form_error_message(error: ValidationError) -> str:
    error_dict = getattr(error, "error_dict", None)
    if error_dict:
        parts: list[str] = []
        for messages_for_field in error.message_dict.values():
            parts.extend(str(item) for item in messages_for_field)
        return " ".join(parts)
    return " ".join(error.messages)


class StationListView(ViewStationRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "infrastructure/station_list.html", _station_list_context(request))


class StationDetailView(ViewStationRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        station = get_object_or_404(Station, pk=pk)
        marker = {
            "id": str(station.pk),
            "name": station.name,
            "code": station.code,
            "city": station.city,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "url": request.path,
        }
        return render(
            request,
            "infrastructure/station_detail.html",
            {
                "station": station,
                "lines": lines_for_station(station),
                "station_markers": [marker],
            },
        )


class StationCreateView(AddStationRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "infrastructure/station_form.html",
            {"form": StationForm(), "title": "Create station"},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = StationForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "infrastructure/station_form.html",
                {"form": form, "title": "Create station"},
            )
        actor = require_authenticated_user(request.user)
        station = create_station(
            actor=actor,
            name=form.cleaned_data["name"],
            code=form.cleaned_data["code"],
            city=form.cleaned_data["city"],
            location=form.cleaned_data["location"],
            is_active=form.cleaned_data.get("is_active", True),
        )
        messages.success(request, f"Station {station.code} created.")
        return redirect("station_detail", pk=station.pk)


class StationUpdateView(ChangeStationRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        station = get_object_or_404(Station, pk=pk)
        return render(
            request,
            "infrastructure/station_form.html",
            {
                "form": StationForm(instance=station),
                "title": f"Edit {station.name}",
                "station": station,
            },
        )

    def post(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        station = get_object_or_404(Station, pk=pk)
        form = StationForm(request.POST, instance=station)
        if not form.is_valid():
            return render(
                request,
                "infrastructure/station_form.html",
                {"form": form, "title": f"Edit {station.name}", "station": station},
            )
        actor = require_authenticated_user(request.user)
        try:
            update_station(
                actor=actor,
                station=station,
                name=form.cleaned_data["name"],
                code=form.cleaned_data["code"],
                city=form.cleaned_data["city"],
                location=form.cleaned_data["location"],
                is_active=form.cleaned_data.get("is_active", True),
            )
        except ValidationError as error:
            messages.error(request, _form_error_message(error))
            return render(
                request,
                "infrastructure/station_form.html",
                {"form": form, "title": f"Edit {station.name}", "station": station},
            )
        messages.success(request, f"Station {station.code} updated.")
        return redirect("station_detail", pk=station.pk)


class StationDeactivateView(ChangeStationRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        station = get_object_or_404(Station, pk=pk)
        return render(
            request,
            "infrastructure/station_confirm_deactivate.html",
            {"station": station},
        )

    def post(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        station = get_object_or_404(Station, pk=pk)
        actor = require_authenticated_user(request.user)
        deactivate_station(actor=actor, station=station)
        messages.success(request, f"Station {station.code} deactivated.")
        return redirect("station_detail", pk=station.pk)


class RailwayLineListView(ViewRailwayLineRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "infrastructure/line_list.html",
            _line_list_context(request),
        )


class RailwayLineDetailView(ViewRailwayLineRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        line = get_object_or_404(
            RailwayLine.objects.select_related("start_station", "end_station"),
            pk=pk,
        )
        return render(request, "infrastructure/line_detail.html", {"line": line})


class RailwayLineCreateView(AddRailwayLineRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "infrastructure/line_form.html",
            {"form": RailwayLineForm(), "title": "Create railway line"},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = RailwayLineForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "infrastructure/line_form.html",
                {"form": form, "title": "Create railway line"},
            )
        actor = require_authenticated_user(request.user)
        line = create_railway_line(
            actor=actor,
            name=form.cleaned_data["name"],
            code=form.cleaned_data["code"],
            start_station=form.cleaned_data["start_station"],
            end_station=form.cleaned_data["end_station"],
            is_active=form.cleaned_data.get("is_active", True),
        )
        messages.success(request, f"Railway line {line.code} created.")
        return redirect("railway_line_detail", pk=line.pk)


class RailwayLineUpdateView(ChangeRailwayLineRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        line = get_object_or_404(
            RailwayLine.objects.select_related("start_station", "end_station"),
            pk=pk,
        )
        return render(
            request,
            "infrastructure/line_form.html",
            {
                "form": RailwayLineForm(instance=line),
                "title": f"Edit {line.name}",
                "line": line,
            },
        )

    def post(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        line = get_object_or_404(
            RailwayLine.objects.select_related("start_station", "end_station"),
            pk=pk,
        )
        form = RailwayLineForm(request.POST, instance=line)
        if not form.is_valid():
            return render(
                request,
                "infrastructure/line_form.html",
                {"form": form, "title": f"Edit {line.name}", "line": line},
            )
        actor = require_authenticated_user(request.user)
        try:
            update_railway_line(
                actor=actor,
                line=line,
                name=form.cleaned_data["name"],
                code=form.cleaned_data["code"],
                start_station=form.cleaned_data["start_station"],
                end_station=form.cleaned_data["end_station"],
                is_active=form.cleaned_data.get("is_active", True),
            )
        except ValidationError as error:
            messages.error(request, _form_error_message(error))
            return render(
                request,
                "infrastructure/line_form.html",
                {"form": form, "title": f"Edit {line.name}", "line": line},
            )
        messages.success(request, f"Railway line {line.code} updated.")
        return redirect("railway_line_detail", pk=line.pk)


class RailwayLineDeactivateView(ChangeRailwayLineRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        line = get_object_or_404(RailwayLine, pk=pk)
        return render(
            request,
            "infrastructure/line_confirm_deactivate.html",
            {"line": line},
        )

    def post(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        line = get_object_or_404(RailwayLine, pk=pk)
        actor = require_authenticated_user(request.user)
        deactivate_railway_line(actor=actor, line=line)
        messages.success(request, f"Railway line {line.code} deactivated.")
        return redirect("railway_line_detail", pk=line.pk)
