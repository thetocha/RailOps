# RailOps architecture

**Status:** Phase 1 foundation plus Phase 2 authentication exist (Django project, PostGIS, custom user, health, session login, role groups). Domain modules (stations, incidents, …) are still planning-only.  
**Date:** 2026-11-09  
**Audience:** Developers inheriting this repository.

This document records architectural decisions for the Railway Operations & Analytics Platform (RailOps). Phase 1 created the Django project; domain modules remain planning-only until later phases.

## 1. Product and scope

RailOps is an **internal** operations and analytics tool for railway personnel. It is not a public booking site, not a signalling/control system, and not safety-critical.

**In scope:** authentication and roles; stations and railway lines; incident lifecycle with immutable history; timetable import; delay tracking; analytics; REST API v1; PDF monthly report; geospatial station/incident views; tests; Docker; CI.

**Out of scope:** tickets, payments, real-time GPS, train control, passenger accounts, mobile apps, microservices, ML, public unauthenticated API, enterprise SSO.

## 2. Why a modular monolith

A single Django process and a single PostgreSQL/PostGIS database own all modules. Apps are split by **business capability**, not by technical layer (no “services repo” vs “API repo”).

Reasons:

- One deployable MVP, one transaction boundary, one permission model.
- Incident history, timetable sync, and reports share stations and users; splitting those into services would add network and consistency cost with no operational benefit.
- Interview and maintenance goal is a coherent Django application, not a distributed system.

See [ADR-001](decisions/ADR-001-modular-monolith.md).

## 3. Why Django

Django provides authentication, ORM, migrations, admin (restricted), forms, templates, and GeoDjango in one stack. Django REST Framework sits on the same models and permission groups. Server-rendered HTML is the primary UI; the API is a first-class second interface, not a separate product.

**Chosen framework release (verified 2026-11-09 against djangoproject.com):**

| Item | Value | Evidence |
|---|---|---|
| Current official Django | 6.1.3 | https://www.djangoproject.com/download/ |
| Python on this machine | 3.13.14 | `python --version` |
| Django 6.1 Python support | 3.12, 3.13, 3.14, 3.15 (3.15 from 6.1.3) | https://docs.djangoproject.com/en/stable/faq/install/ |
| Django 5.2 LTS | 5.2.19; Python 3.10–3.14; **mainstream ended 2025-12-03**; extended until April 2028 | same sources |

**Decision:** target **Django 6.1.x** (pin the latest 6.1 patch at Phase 1 install) on **Python 3.13**. There is **no Python 3.13 incompatibility** with current Django. Django 5.2 remains a security-supported LTS fallback if a third-party package (DRF, django-stubs, WeasyPrint stack) cannot yet support 6.1 — that fallback is a Phase 1 install-time check, not an assumption.

See also [ADR-002](decisions/ADR-002-postgresql-postgis.md) for the database.

## 4. Runtime topology

```text
Browser  -->  Nginx (prod)  -->  Gunicorn  -->  Django (modular monolith)
                                         |
                                         v
                              PostgreSQL + PostGIS

Dev: Django runserver (or container) + PostGIS via Docker Compose.
PDF files: object/local media storage, not PostgreSQL BYTEA.
External timetable: adapter (mock / CSV / optional HTTPX client).
```

Do not run `runserver` in production. Do not auto-migrate on every worker start.

## 5. Application boundaries

Target layout under `railops/` (created in Phase 1, not now):

| App | Owns | Must not own |
|---|---|---|
| `accounts` | Custom user, groups/roles, login/password, user admin | Incident or station business rules |
| `infrastructure` | Station, RailwayLine, spatial queries on stations | Incidents, timetables |
| `incidents` | Incident, IncidentEvent, status transitions, assignment | User management, PDF files |
| `timetables` | TrainService, ScheduledStop, Delay derivation/storage | HTTP to third parties |
| `integrations` | Provider interface, mock, CSV, HTTPX client, ExternalSyncRun, sync command | Direct writes from views to timetable models without the sync service |
| `analytics` | Query/aggregation + Pandas transformations + typed metrics | HTML chrome, PDF bytes |
| `reports` | Report records, WeasyPrint generation, download auth | Recalculating analytics independently of `analytics` |

`config/` holds settings (development / test / production), URLs, WSGI/ASGI.

Cross-app rule: **depend downward** (HTTP → services → models). Incidents may FK to infrastructure and accounts. Integrations persist through timetable services. Analytics **reads** incidents and timetables; it does not write operational records. Reports call analytics, then render PDF.

Avoid circular imports. If two apps need a shared type, put it in a small `apps/common` only when duplication is real — do not create `common` in Phase 1 unless needed.

## 6. Layer conventions

```text
HTTP / API / Templates
        |
        v
    Services
        |
        v
  Models / ORM
        |
        v
 PostgreSQL / PostGIS
```

| Layer | Responsibility | Forbidden |
|---|---|---|
| Models | Schema, constraints, simple invariants, `__str__` | Full workflows, HTTP |
| Services | Writes, transitions, sync, transactions | Request objects as required args |
| Selectors | Non-trivial reads, `select_related`/`prefetch_related` | One-off trivial `objects.get` wrappers |
| Views | Authz, forms/serializers, call service/selector, HTTP | Status-machine logic, PDF math |
| Serializers / forms | Input validation and representation | Persistence side effects beyond `save` of the validated instance |
| Integration adapters | I/O, timeouts, payload validation (Pydantic or equivalent) | Skipping validation before ORM |

**Incident transition (canonical service shape):**

```python
def transition_incident(
    *,
    incident_id: UUID,
    new_status: Incident.Status,
    actor: User,
    comment: str | None = None,
) -> Incident: ...
```

Must: exist check, permission, legal transition, row lock (`select_for_update` on the incident row), update, immutable `IncidentEvent`, one transaction.

## 7. Integration adapter

```text
IntegrationService
        |
        v
RailwayProviderInterface
        |
        +-- MockRailwayProvider      # deterministic local/CI
        +-- CSVRailwayProvider       # operator fallback
        +-- ExternalRailwayAPIClient # HTTPX; only if a licensed, documented source exists
```

Phase 5 must **not** scrape unofficial endpoints or present them as a production railway API. Investigation for Phase 0: many national APIs (e.g. GB Darwin, some operator RIS APIs) require contracts and keys; GTFS/NeTEx feeds exist under **operator-specific licences**. Default MVP path is **mock + CSV**. An HTTPX client is built against the same interface so a real feed can be added when licence and auth are explicit.

See [ADR-003](decisions/ADR-003-external-integration.md).

## 8. Analytics vs ORM

- **PostgreSQL/ORM:** counts, filters, date-bounded lists, spatial distance, routine dashboard totals.
- **Pandas:** multi-series report tables, median/percentile style metrics once a **bounded** record set is already filtered in SQL, combining incident and delay frames for the monthly PDF.

Do not load unbounded tables into memory. Do not use Pandas for `COUNT(*)` that SQL already does. Typed result objects (`IncidentMetrics`, `DelayMetrics`) are returned to views — not raw DataFrames.

On-time threshold (planning default): **delay ≤ 300 seconds** counts as on time. Missing actual times are **excluded** from delay statistics, never treated as zero. See [database-design](database-design.md) and [ADR-005](decisions/ADR-005-analytics-pandas.md).

## 9. PDF flow

```text
Permissioned request
  -> validate period (max range, e.g. 31 days for “monthly”)
  -> analytics services
  -> HTML report template
  -> WeasyPrint
  -> store file in MEDIA (configurable storage)
  -> Report row (status, path, timestamps)
  -> authorised download
```

No HTML string concatenation for the document body. No arbitrary remote assets during render. Failed generation is recorded on `Report`, not swallowed.

See [ADR-006](decisions/ADR-006-pdf-generation.md).

## 10. Geospatial

GeoDjango + PostGIS. Station `location` is `PointField` SRID **4326**, `geography=True` where distance-in-metres is required. Spatial index via migration (GIST). Two required queries: stations within radius; nearest station. Leaflet + OSM-compatible tiles for the map; **tile usage terms must be checked before production** (public OSM tile servers are not a blank cheque). Tests use PostGIS, never SQLite.

## 11. Frontend

Django templates, Bootstrap 5, vanilla JS, Chart.js, Leaflet. **No React, no SPA build.** Progressive enhancement: lists, forms, and reports work without JS; charts/maps enhance.

Navigation visibility follows Django permissions; **hiding a link is not access control**.

See [ADR-004](decisions/ADR-004-server-rendered-frontend.md).

## 12. Security boundaries

| Boundary | Rule |
|---|---|
| Identity | Django auth; custom `AbstractUser`; no homemade password hashes; no JWT required for HTML MVP |
| Roles | Groups: Administrator, Dispatcher, Viewer + Django permissions |
| Sessions | Secure cookies in production; CSRF on; `ALLOWED_HOSTS` and CSRF trusted origins from env |
| Secrets | Environment / secret manager; `.env` never committed; `.env.example` placeholders only |
| API | Session auth for browser MVP; per-action permissions; no stack traces; OpenAPI via drf-spectacular |
| Files | Reports outside source tree; path traversal rejected; download re-checks permission |
| Integrations | Timeouts, no retry of auth failures, no logging of keys or full sensitive payloads |
| Admin | Django admin restricted to administrators |

## 13. Quality and delivery

Ruff, mypy (application code), Bandit, pip-audit, pytest + pytest-django, GitHub Actions with PostGIS service. Coverage target: ≥ 80% of business logic, with explicit permission and transition tests.

## 14. Assumptions vs facts

| Claim | Status |
|---|---|
| Workspace contains only `AGENTS.md`; no Django project, no git | **Fact** (inspected 2026-11-09) |
| Python 3.13.14, uv 0.12.7, pip 26.1.2, Docker 29.7.2 | **Fact** (commands run) |
| Django 6.1.3 supports Python 3.13 | **Fact** (official FAQ) |
| Exact DRF / WeasyPrint / pandas / GDAL wheel versions on Windows | **Unverified** — resolve with uv in Phase 1 |
| A licensed live railway API will be available for the demo | **Not assumed** — mock + CSV is the default |
| OSM tiles for unrestricted production | **Not assumed** |
