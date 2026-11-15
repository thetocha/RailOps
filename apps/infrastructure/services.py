"""Station and railway-line write operations. Views must not duplicate this logic."""

from __future__ import annotations

import logging

from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.accounts.permissions import require_authenticated_user
from apps.infrastructure.codes import normalize_infrastructure_code
from apps.infrastructure.models import RailwayLine, Station
from apps.infrastructure.permissions import (
    PERM_ADD_RAILWAY_LINE,
    PERM_ADD_STATION,
    PERM_CHANGE_RAILWAY_LINE,
    PERM_CHANGE_STATION,
)

logger = logging.getLogger(__name__)


def _assert_perm(actor: User, perm: str) -> None:
    if not actor.has_perm(perm):
        raise PermissionDenied


def _station_unique_code_error() -> ValidationError:
    return ValidationError({"code": "A station with this code already exists."})


def _line_unique_code_error() -> ValidationError:
    return ValidationError({"code": "A railway line with this code already exists."})


@transaction.atomic
def create_station(
    *,
    actor: User,
    name: str,
    code: str,
    city: str,
    location: Point,
    is_active: bool = True,
) -> Station:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_ADD_STATION)
    cleaned_code = normalize_infrastructure_code(code)
    cleaned_name = name.strip()
    cleaned_city = city.strip()
    if not cleaned_name:
        raise ValidationError({"name": "Name is required."})
    if not cleaned_city:
        raise ValidationError({"city": "City is required."})
    try:
        station = Station.objects.create(
            name=cleaned_name,
            code=cleaned_code,
            city=cleaned_city,
            location=location,
            is_active=is_active,
        )
    except IntegrityError as exc:
        raise _station_unique_code_error() from exc
    logger.info("Created station code=%s actor=%s", station.code, actor.username)
    return station


@transaction.atomic
def update_station(
    *,
    actor: User,
    station: Station,
    name: str,
    code: str,
    city: str,
    location: Point,
    is_active: bool,
) -> Station:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_CHANGE_STATION)
    cleaned_code = normalize_infrastructure_code(code)
    cleaned_name = name.strip()
    cleaned_city = city.strip()
    if not cleaned_name:
        raise ValidationError({"name": "Name is required."})
    if not cleaned_city:
        raise ValidationError({"city": "City is required."})
    station.name = cleaned_name
    station.code = cleaned_code
    station.city = cleaned_city
    station.location = location
    station.is_active = is_active
    try:
        station.save()
    except IntegrityError as exc:
        raise _station_unique_code_error() from exc
    logger.info("Updated station code=%s actor=%s", station.code, actor.username)
    return station


@transaction.atomic
def deactivate_station(*, actor: User, station: Station) -> Station:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_CHANGE_STATION)
    if not station.is_active:
        return station
    station.is_active = False
    station.save(update_fields=["is_active", "updated_at"])
    logger.info("Deactivated station code=%s actor=%s", station.code, actor.username)
    return station


@transaction.atomic
def create_railway_line(
    *,
    actor: User,
    name: str,
    code: str,
    start_station: Station,
    end_station: Station,
    is_active: bool = True,
) -> RailwayLine:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_ADD_RAILWAY_LINE)
    cleaned_code = normalize_infrastructure_code(code)
    cleaned_name = name.strip()
    if not cleaned_name:
        raise ValidationError({"name": "Name is required."})
    if not start_station.is_active:
        raise ValidationError({"start_station": "Choose an active start station."})
    if not end_station.is_active:
        raise ValidationError({"end_station": "Choose an active end station."})
    try:
        line = RailwayLine.objects.create(
            name=cleaned_name,
            code=cleaned_code,
            start_station=start_station,
            end_station=end_station,
            is_active=is_active,
        )
    except IntegrityError as exc:
        raise _line_unique_code_error() from exc
    logger.info("Created railway line code=%s actor=%s", line.code, actor.username)
    return line


@transaction.atomic
def update_railway_line(
    *,
    actor: User,
    line: RailwayLine,
    name: str,
    code: str,
    start_station: Station,
    end_station: Station,
    is_active: bool,
) -> RailwayLine:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_CHANGE_RAILWAY_LINE)
    cleaned_code = normalize_infrastructure_code(code)
    cleaned_name = name.strip()
    if not cleaned_name:
        raise ValidationError({"name": "Name is required."})
    if not start_station.is_active and start_station.pk != line.start_station_id:
        raise ValidationError({"start_station": "Choose an active start station."})
    if not end_station.is_active and end_station.pk != line.end_station_id:
        raise ValidationError({"end_station": "Choose an active end station."})
    line.name = cleaned_name
    line.code = cleaned_code
    line.start_station = start_station
    line.end_station = end_station
    line.is_active = is_active
    try:
        line.save()
    except IntegrityError as exc:
        raise _line_unique_code_error() from exc
    logger.info("Updated railway line code=%s actor=%s", line.code, actor.username)
    return line


@transaction.atomic
def deactivate_railway_line(*, actor: User, line: RailwayLine) -> RailwayLine:
    actor = require_authenticated_user(actor)
    _assert_perm(actor, PERM_CHANGE_RAILWAY_LINE)
    if not line.is_active:
        return line
    line.is_active = False
    line.save(update_fields=["is_active", "updated_at"])
    logger.info("Deactivated railway line code=%s actor=%s", line.code, actor.username)
    return line
