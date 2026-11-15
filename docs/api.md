# REST API

**Status:** Phase 6. Stations, incidents, and train services are implemented. Analytics and report endpoints are Phase 7 and Phase 9.

Base path: `/api/v1/`. Django REST Framework 3.18.3, OpenAPI via drf-spectacular, **session authentication**. There is no public unauthenticated API.

## Authentication

Sign in through `/accounts/login/` (session cookie). Browsable API and Swagger (`/api/docs/`) use the same session. Unsafe methods require CSRF, matching Django’s session auth.

Unauthenticated requests to `/api/` return **401** JSON (`WWW-Authenticate: Session`). HTML `LoginRequiredMiddleware` does not redirect API paths. Authenticated users without the required permission receive **403**.

## Permissions

Django model permissions, not role-name checks.

| Role | Stations | Incidents | Train services |
|---|---|---|---|
| Viewer | GET | GET | GET |
| Dispatcher | GET | GET, POST, PATCH, transition | GET |
| Administrator | GET, POST, PATCH | GET, POST, PATCH, transition, reopen closed | GET |

Hiding UI is not enforcement. Viewers receive 403 on writes.

## Endpoints

### Stations

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/stations/` | List (paginated). `search`/`q`, `is_active` |
| GET | `/api/v1/stations/{id}/` | Detail (latitude/longitude, not WKT) |
| POST | `/api/v1/stations/` | Create |
| PATCH | `/api/v1/stations/{id}/` | Update |

Coordinates are WGS84 latitude/longitude. Writes go through `create_station` / `update_station`.

### Incidents

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/incidents/` | List. `search`/`q`, `status`, `severity`, `category`, `station` |
| GET | `/api/v1/incidents/{id}/` | Detail including immutable `events` |
| POST | `/api/v1/incidents/` | Register |
| PATCH | `/api/v1/incidents/{id}/` | Update fields / assignment |
| POST | `/api/v1/incidents/{id}/transition/` | Body: `{"status": "in_progress", "comment": ""}` |

Invalid transitions return 400. Closed reopen still requires `incidents.reopen_closed_incident`.

### Train services

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/services/` | List. `date`/`service_date`, `station`, `search`/`q` |
| GET | `/api/v1/services/{id}/` | Detail including stops and delays |
| GET | `/api/v1/services/{id}/stops/` | Scheduled stops |

No write endpoints. Import remains `sync_timetables`.

### Schema

| Method | Path | Description |
|---|---|---|
| GET | `/api/schema/` | OpenAPI schema (authenticated) |
| GET | `/api/docs/` | Swagger UI (authenticated) |

## Pagination

Page number pagination, 20 items, `page_size` up to 100. List envelopes: `count`, `next`, `previous`, `results`.

## Errors

JSON bodies. Field errors use DRF’s `{ "field": ["message"] }`. Non-field errors use `{ "detail": "..." }`. Unhandled exceptions return a generic 500 `detail` without stack traces.

## Not in Phase 6

`/api/v1/analytics/*` and `/api/v1/reports/*` are implemented with analytics (Phase 7) and PDF reports (Phase 9).
