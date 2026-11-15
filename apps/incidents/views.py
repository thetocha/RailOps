"""HTTP adapters for incidents. Writes go through services."""

from __future__ import annotations

from uuid import UUID

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.http import remaining_querystring
from apps.accounts.models import User
from apps.accounts.permissions import require_authenticated_user
from apps.incidents.forms import (
    IncidentAssignForm,
    IncidentForm,
    IncidentSeverityForm,
    IncidentTransitionForm,
)
from apps.incidents.models import Incident
from apps.incidents.permissions import (
    PERM_REOPEN_CLOSED,
    AddIncidentRequiredMixin,
    ChangeIncidentRequiredMixin,
    ViewIncidentRequiredMixin,
)
from apps.incidents.selectors import (
    allowed_next_statuses,
    events_for_incident,
    incident_directory,
)
from apps.incidents.services import (
    assign_incident,
    change_incident_severity,
    create_incident,
    transition_incident,
    update_incident,
)
from apps.infrastructure.models import Station

ITEMS_PER_PAGE = 20


def _parse_uuid(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def _choice_or_none(raw: str | None, allowed: set[str]) -> str | None:
    if raw in allowed:
        return raw
    return None


def _incident_list_context(request: HttpRequest) -> dict[str, object]:
    search = request.GET.get("q", "")
    status = _choice_or_none(request.GET.get("status"), set(Incident.Status.values))
    severity = _choice_or_none(request.GET.get("severity"), set(Incident.Severity.values))
    category = _choice_or_none(request.GET.get("category"), set(Incident.Category.values))
    station_id = _parse_uuid(request.GET.get("station"))
    paginator = Paginator(
        incident_directory(
            search=search,
            status=status,
            severity=severity,
            category=category,
            station_id=station_id,
        ),
        ITEMS_PER_PAGE,
    )
    page = paginator.get_page(request.GET.get("page"))
    return {
        "page": page,
        "search": search,
        "status": status or "",
        "severity": severity or "",
        "category": category or "",
        "station_id": str(station_id) if station_id else "",
        "status_choices": Incident.Status.choices,
        "severity_choices": Incident.Severity.choices,
        "category_choices": Incident.Category.choices,
        "stations": Station.objects.order_by("name"),
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


def _detail_context(request: HttpRequest, incident: Incident) -> dict[str, object]:
    actor = require_authenticated_user(request.user)
    next_statuses = allowed_next_statuses(
        current=Incident.Status(incident.status),
        can_reopen_closed=actor.has_perm(PERM_REOPEN_CLOSED),
    )
    assign_form = IncidentAssignForm(initial={"assigned_to": incident.assigned_to_id})
    return {
        "incident": incident,
        "events": events_for_incident(incident),
        "transition_form": IncidentTransitionForm(allowed_statuses=next_statuses),
        "assign_form": assign_form,
        "severity_form": IncidentSeverityForm(initial={"severity": incident.severity}),
        "next_statuses": next_statuses,
    }


class IncidentListView(ViewIncidentRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "incidents/incident_list.html", _incident_list_context(request))


class IncidentDetailView(ViewIncidentRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        incident = get_object_or_404(
            Incident.objects.select_related(
                "station",
                "railway_line",
                "reporter",
                "assigned_to",
            ),
            pk=pk,
        )
        return render(request, "incidents/incident_detail.html", _detail_context(request, incident))


class IncidentCreateView(AddIncidentRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "incidents/incident_form.html",
            {"form": IncidentForm(), "title": "Register incident"},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = IncidentForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "incidents/incident_form.html",
                {"form": form, "title": "Register incident"},
            )
        actor = require_authenticated_user(request.user)
        incident = create_incident(
            actor=actor,
            title=form.cleaned_data["title"],
            description=form.cleaned_data["description"],
            station=form.cleaned_data["station"],
            railway_line=form.cleaned_data.get("railway_line"),
            category=Incident.Category(form.cleaned_data["category"]),
            severity=Incident.Severity(form.cleaned_data["severity"]),
        )
        messages.success(request, "Incident registered.")
        return redirect("incident_detail", pk=incident.pk)


class IncidentUpdateView(ChangeIncidentRequiredMixin, View):
    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        incident = get_object_or_404(Incident, pk=pk)
        return render(
            request,
            "incidents/incident_form.html",
            {
                "form": IncidentForm(instance=incident),
                "title": f"Edit {incident.title}",
                "incident": incident,
            },
        )

    def post(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        incident = get_object_or_404(Incident, pk=pk)
        form = IncidentForm(request.POST, instance=incident)
        if not form.is_valid():
            return render(
                request,
                "incidents/incident_form.html",
                {"form": form, "title": f"Edit {incident.title}", "incident": incident},
            )
        actor = require_authenticated_user(request.user)
        try:
            update_incident(
                actor=actor,
                incident_id=incident.pk,
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                station=form.cleaned_data["station"],
                railway_line=form.cleaned_data.get("railway_line"),
                category=Incident.Category(form.cleaned_data["category"]),
                severity=Incident.Severity(form.cleaned_data["severity"]),
            )
        except ValidationError as error:
            messages.error(request, _form_error_message(error))
            return render(
                request,
                "incidents/incident_form.html",
                {"form": form, "title": f"Edit {incident.title}", "incident": incident},
            )
        messages.success(request, "Incident updated.")
        return redirect("incident_detail", pk=incident.pk)


class IncidentTransitionView(ChangeIncidentRequiredMixin, View):
    def post(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        incident = get_object_or_404(Incident, pk=pk)
        actor = require_authenticated_user(request.user)
        next_statuses = allowed_next_statuses(
            current=Incident.Status(incident.status),
            can_reopen_closed=actor.has_perm(PERM_REOPEN_CLOSED),
        )
        form = IncidentTransitionForm(request.POST, allowed_statuses=next_statuses)
        if not form.is_valid():
            messages.error(request, "Choose a valid status.")
            return redirect("incident_detail", pk=incident.pk)
        try:
            transition_incident(
                incident_id=incident.pk,
                new_status=Incident.Status(form.cleaned_data["new_status"]),
                actor=actor,
                comment=form.cleaned_data.get("comment") or None,
            )
        except ValidationError as error:
            messages.error(request, _form_error_message(error))
            return redirect("incident_detail", pk=incident.pk)
        messages.success(request, "Incident status updated.")
        return redirect("incident_detail", pk=incident.pk)


class IncidentAssignView(ChangeIncidentRequiredMixin, View):
    def post(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        incident = get_object_or_404(Incident, pk=pk)
        form = IncidentAssignForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Choose a valid assignee.")
            return redirect("incident_detail", pk=incident.pk)
        actor = require_authenticated_user(request.user)
        assignee = cast_user(form.cleaned_data.get("assigned_to"))
        try:
            assign_incident(
                actor=actor,
                incident_id=incident.pk,
                assignee=assignee,
                comment=form.cleaned_data.get("comment") or None,
            )
        except ValidationError as error:
            messages.error(request, _form_error_message(error))
            return redirect("incident_detail", pk=incident.pk)
        messages.success(request, "Incident assignment updated.")
        return redirect("incident_detail", pk=incident.pk)


class IncidentSeverityView(ChangeIncidentRequiredMixin, View):
    def post(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        incident = get_object_or_404(Incident, pk=pk)
        form = IncidentSeverityForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Choose a valid severity.")
            return redirect("incident_detail", pk=incident.pk)
        actor = require_authenticated_user(request.user)
        try:
            change_incident_severity(
                actor=actor,
                incident_id=incident.pk,
                severity=Incident.Severity(form.cleaned_data["severity"]),
                comment=form.cleaned_data.get("comment") or None,
            )
        except ValidationError as error:
            messages.error(request, _form_error_message(error))
            return redirect("incident_detail", pk=incident.pk)
        messages.success(request, "Incident severity updated.")
        return redirect("incident_detail", pk=incident.pk)


def cast_user(value: object) -> User | None:
    if value is None:
        return None
    if isinstance(value, User):
        return value
    raise ValidationError("Invalid assignee.")
