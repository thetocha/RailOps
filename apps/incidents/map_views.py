"""HTTP adapters for the operations map. Spatial work lives in spatial/map modules."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from apps.incidents.map import OperationsMap, build_operations_map
from apps.incidents.permissions import PERM_VIEW_INCIDENT
from apps.infrastructure.forms import NearbySearchForm
from apps.infrastructure.permissions import ViewStationRequiredMixin


class OperationsMapView(ViewStationRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        requested = any(key in request.GET for key in ("latitude", "longitude", "radius_meters"))
        form = NearbySearchForm(request.GET) if requested else NearbySearchForm()
        include_incidents = request.user.has_perm(PERM_VIEW_INCIDENT)
        snapshot: OperationsMap | None = None
        if form.is_bound and form.is_valid():
            snapshot = build_operations_map(
                longitude=form.cleaned_data["longitude"],
                latitude=form.cleaned_data["latitude"],
                radius_meters=form.cleaned_data["radius_meters"],
                include_incidents=include_incidents,
            )
        elif not form.is_bound:
            snapshot = build_operations_map(include_incidents=include_incidents)
        return render(
            request,
            "incidents/operations_map.html",
            {
                "form": form,
                "snapshot": snapshot,
                "map_payload": {
                    "origin": None if snapshot is None else snapshot.origin,
                    "stations": [] if snapshot is None else list(snapshot.stations),
                    "incidents": [] if snapshot is None else list(snapshot.incidents),
                },
            },
        )
