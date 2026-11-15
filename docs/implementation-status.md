# Implementation status

**Updated:** 2026-11-15  
**Current phase:** Phase 6 REST API complete on this branch. Analytics and reports APIs remain Phase 7 and Phase 9.

## Phase 1 — Project foundation

**Status:** Complete (see previous update). 20 foundation tests remain part of the suite.

## Phase 2 — Authentication and permissions

**Objective:** Login/logout, password change and reset, Django Groups for Administrator / Dispatcher / Viewer, permission-based access control, administrator user management, tests.

**Files affected (created or updated):**

- `apps/accounts/models.py` — custom User permissions catalog
- `apps/accounts/permissions.py` — group names, helpers, mixins, `ensure_role_groups`
- `apps/accounts/services.py` — create/update/deactivate user (no request objects)
- `apps/accounts/selectors.py` — user directory query
- `apps/accounts/forms.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `signals.py`
- `apps/accounts/management/commands/seed_role_groups.py`
- `apps/accounts/migrations/0002_user_operational_permissions.py`
- `apps/accounts/tests/` — auth, permissions, user management
- `config/urls.py`, `config/health.py`, `config/settings/{base,development,test,production}.py`
- `templates/` — base, login/password, dashboard, user management
- `static/css/app.css`
- `.env.example`
- `docs/implementation-status.md`, `docs/development-guide.md`, `README.md`

**Implementation details:**

- Session authentication for HTML. No JWT.
- `LoginRequiredMiddleware` redirects anonymous users to login. `GET /health/` is `@login_not_required`.
- Roles are Django Groups. Views check `user.has_perm(...)` / mixins, not group names.
- Groups are seeded by `post_migrate` on the accounts app (`ensure_role_groups`). The same function is the `seed_role_groups` management command. Idempotent. Failures are not swallowed. Only `accounts.user` permissions are added/removed; later apps can attach their own model permissions to the same groups.
- Passwords use Django hashers only. User forms never display the stored hash.
- Development email: console backend via `MAILERS`. Production: SMTP via `MAILERS` OPTIONS (`EMAIL_HOST` env vars). Django 6 forbids combining `MAILERS` with deprecated `EMAIL_BACKEND` as a setting.
- User management: list/search/paginate, create, update, deactivate. Dispatcher and Viewer receive HTTP 403.

**Tests added or updated:**

- Unauthenticated redirect from dashboard, user list, password change
- Viewer cannot create/update users (403)
- Dispatcher cannot manage users (403) and cannot use Django admin (`is_staff` is false)
- Role Administrator is not staff; staff-but-not-superuser cannot escalate via `/admin/`
- Deactivated users lose sessions and are redirected to login from dashboard and password-change
- Unique non-blank email; `/health/` exempt from SSL redirect; production image defaults to production settings
- Administrator can create a user and assign Dispatcher
- Direct `manage_users` permission (without Administrator group) can open the user list
- Login/logout and password change happy paths
- Password reset does not leak whether an email exists; token confirm sets a new password
- Stored password uses a hasher prefix (`identify_hasher`)
- CSRF POST without token → 403
- Groups catalog and stale-permission repair

**Commands executed and results:**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `docker compose up -d` | App republished on host **8001**, DB **5433** |
| `docker compose exec app python manage.py migrate` | Applied `accounts.0002_user_operational_permissions` |
| `docker compose exec app python manage.py seed_role_groups` | Role groups ensured |
| `docker compose exec … app pytest` | **47 passed** |
| `docker compose exec … app mypy` | Success: no issues found in 44 source files |
| `curl http://127.0.0.1:8001/health/` | `{"status":"ok"}` |
| `curl http://127.0.0.1:8001/accounts/login/` | HTTP 200, CSRF + password field present |
| `curl http://127.0.0.1:8001/` | HTTP 302 to login |
| `docker compose exec … app python manage.py check` | `gis.W001` only (GDAL 3.6.2, known from Phase 1) |

## Phase 2 follow-up — Bugbot findings

**Status:** Implemented on the Phase 2 codebase. Phase 3 was not started.

| Finding | Fix |
|---|---|
| High — Django admin privilege escalation | `sync_staff_flag()` grants `is_staff` only to superusers. `AdminSite.has_permission` and User/Group ModelAdmins are superuser-only. Role Administrators use `/accounts/users/`. |
| Medium — deactivated sessions | `deactivate_user` / `update_user(..., is_active=False)` delete that user's DB sessions. `ActiveUserSessionMiddleware` logs out authenticated inactive users. |
| Medium — production image settings | Dockerfile `ENV DJANGO_SETTINGS_MODULE=config.settings.production`. Compose still sets development for local runserver. |
| Low — duplicate emails | Partial unique constraint `accounts_user_unique_email` (blank emails allowed). Forms reject duplicates. |
| Low — role drift | Group admin is superuser-only. `seed_role_groups` remains the idempotent source of truth for `accounts.user` perms. |
| Low — CSRF port 8001 | Development settings merge localhost/127.0.0.1 for ports 8000 and `APP_PUBLISH_PORT`. `.env.example` lists both. |
| Low — `/health/` SSL redirect | Production `SECURE_REDIRECT_EXEMPT = [r"^health/?$"]`. |

**Commands executed and results (follow-up):**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `docker compose exec app python manage.py makemigrations --check --dry-run` | No changes detected |
| `docker compose exec app python manage.py migrate` | Applied `accounts.0003_user_unique_email` |
| `docker compose exec … app pytest` | **63 passed** |
| `docker compose exec … app mypy` | Success: no issues found in 48 source files |

**Remaining limitations (after Phase 2):**

- Incidents, DRF, analytics, PDF, and map UI are **not** implemented (Phase 4+).
- Password-reset email in development is printed to the app container log (console backend). SMTP is configured only in production settings.
- Login UI uses Bootstrap 5 from a CDN. Full dashboard chrome is Phase 8.
- Rate limiting is not implemented.
- Native Windows GDAL/GEOS still missing — pytest/mypy/manage.py stay in Docker on this host.
- Host ports remain 5433 / 8001 on this workstation.

## Acceptance criteria (Phase 2)

| Criterion | Status |
|---|---|
| Login and logout | **Implemented and tested** |
| Password change | **Implemented and tested** |
| Password reset (token; console email in dev) | **Implemented and tested** |
| Groups: Administrator, Dispatcher, Viewer | **Implemented and tested** (`post_migrate` + command) |
| Permissions via Groups, not role-name checks in views | **Implemented and tested** (direct permission grant test) |
| Administrator user management | **Implemented and tested** |
| Viewers cannot modify users | **Implemented and tested** (403) |
| Dispatchers cannot manage users | **Implemented and tested** (403) |
| Unauthenticated users redirected to login | **Implemented and tested** |
| Passwords hashed, never plaintext | **Implemented and tested** |
| CSRF on POSTs | **Implemented and tested** |

## Phase 3 — Railway infrastructure

**Objective:** Station and RailwayLine models, migrations, forms, CRUD views with search/filter/pagination, spatial index, role-based access.

**Files affected (created or updated):**

- `apps/infrastructure/` — models, services, selectors, forms, views, permissions, admin, tests
- `apps/infrastructure/migrations/0001_initial_station_and_railway_line.py`
- `apps/accounts/forms.py` — `apply_bootstrap` shared with infrastructure forms
- `apps/accounts/http.py` — pagination query-string helper
- `apps/accounts/views.py` — user list passes `querystring` into the shared pager
- `config/settings/base.py`, `config/urls.py`
- `templates/base.html`, `templates/dashboard/home.html`, `templates/components/pagination.html`
- `templates/infrastructure/`
- `docs/`, `README.md`, `.github/workflows/ci.yml`, `pyproject.toml`

**Implementation details:**

- `Station` and `RailwayLine` use UUID primary keys, unique codes, `PROTECT` on station FKs, and GeoDjango fields (SRID 4326, `geography=True`). Spatial index is the default GIST index on `Station.location`.
- Geometry on a railway line is optional and never inferred from station coordinates.
- Writes go through services (`create_station`, `update_station`, `deactivate_station`, and the line equivalents). There is no HTML delete path.
- Station codes are normalised to uppercase. Latitude/longitude are validated before constructing a `Point`.
- Permissions: Administrator gets `view/add/change` for both models. Dispatcher and Viewer get `view` only. `delete_*` is not granted. Seeded by infrastructure `post_migrate`.
- List pages support search, active/inactive/all filter, and pagination (20 per page).

**Tests added or updated:**

- Unique codes, empty-code check constraints, timestamps, `__str__`, geography field metadata, GIST index presence
- `PROTECT` prevents deleting a station used as a line endpoint
- Viewer/dispatcher 403 on create/update/deactivate; administrator happy path
- Direct `add_station` permission (without Administrator group) can open create
- CSRF POST without token → 403
- Form coordinate and duplicate-code validation
- Search, status filter, and pagination

**Commands executed and results:**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `uv run mypy` | Success: no issues found in 71 source files |
| `uv run bandit -r apps config scripts -x tests,apps/accounts/tests,apps/infrastructure/tests` | No issues identified |
| `uv run python manage.py check` | `gis.W001` only (GDAL 3.8.4) |
| `uv run pytest` | **101 passed** |

## Acceptance criteria (Phase 3)

| Criterion | Status |
|---|---|
| Stations can be created, updated and deactivated | **Implemented and tested** |
| Railway lines can be managed | **Implemented and tested** |
| Unique station codes are enforced | **Implemented and tested** |
| Geographic coordinates are persisted | **Implemented and tested** |
| Users see only functionality permitted by their role | **Implemented and tested** |
| Spatial index present | **Implemented and tested** |

## Phase 4 — Incident management

**Objective:** Incident lifecycle with immutable history, validated status transitions, assignment, filtering, and role-based access.

**Files affected:** `apps/incidents/` (models, services, selectors, forms, views, permissions, admin, tests), templates, navigation, settings, CI Bandit excludes, docs.

**Implementation details:**

- `Incident` and `IncidentEvent` with UUID keys. Station FK is `PROTECT`; railway line and assignee are `SET_NULL`.
- Allowed transitions: open → in progress → resolved → closed; in progress → open; resolved → in progress (clears `resolved_at`). Closed is terminal except `incidents.reopen_closed_incident` (Administrator).
- `transition_incident` locks the incident row (`select_for_update` on the incident table only — nullable joins are omitted so PostgreSQL accepts `FOR UPDATE`), writes the incident, and inserts an immutable event in one transaction.
- Events cannot be updated or deleted through the model API. History is displayed on the detail page.
- Dispatcher and Administrator can register, update, assign, change severity, and transition. Viewer is read-only.

**Tests added:**

- Transition matrix, invalid transitions, resolved_at set/cleared, closed reopen permission
- Event immutability, station `PROTECT`, check constraint
- Viewer 403 on create/transition; dispatcher happy path; CSRF; list search/filter

**Commands executed and results:**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `uv run mypy` | Success: no issues found in 91 source files |
| `uv run bandit …` | No issues identified |
| `uv run pytest` | **129 passed** |

## Acceptance criteria (Phase 4)

| Criterion | Status |
|---|---|
| Full incident lifecycle works | **Implemented and tested** |
| Every relevant state change is recorded | **Implemented and tested** |
| Invalid transitions are rejected | **Implemented and tested** |
| Unauthorized modifications are rejected | **Implemented and tested** |
| Database consistency is maintained | **Implemented and tested** (`resolved_at` constraint, `PROTECT`, row lock) |

## Phase 5 — Timetable and external integration

**Objective:** TrainService, ScheduledStop, Delay, provider adapter (mock, CSV, HTTPX), idempotent synchronization, ExternalSyncRun, management command, HTML list/detail and sync UI, tests.

**Files affected (created or updated):**

- `apps/timetables/` — models, delay calculation, upsert services, selectors, views, permissions, admin, tests
- `apps/integrations/` — ExternalSyncRun, providers, synchronize_timetables, HTML sync, management command, tests
- `apps/timetables/migrations/0001_initial_train_service_stop_delay.py`
- `apps/integrations/migrations/0001_initial_external_sync_run.py`
- `config/settings/base.py`, `config/urls.py`, `pyproject.toml`, `uv.lock`
- `templates/base.html`, `templates/dashboard/home.html`, `templates/timetables/`, `templates/integrations/`
- `.github/workflows/ci.yml`, `docs/`

**Implementation details:**

- Unique `(external_id, service_date)` and `(train_service, stop_sequence)` make re-import idempotent. Delay rows unique on `(scheduled_stop, kind)`.
- Delay is `actual - scheduled` in seconds (signed). Missing actual timestamps do not create a delay of zero. MVP measured event is arrival when both arrival times exist, otherwise the one complete pair. On-time threshold is 300 seconds.
- `RailwayProvider` protocol: `MockRailwayProvider` (deterministic ICE 501 / RE 42), `CSVRailwayProvider` (invalid rows recorded, valid rows persisted), `ExternalRailwayAPIClient` (HTTPX timeouts, retry of transport/transient errors, `Retry-After`, no retry of 4xx, Pydantic validation). This is not a national railway API.
- `synchronize_timetables` creates `ExternalSyncRun`, validates payloads, persists through timetable services, and never stores credentials or raw payloads. HTML sync is administrator-only (`run_timetable_sync`). Viewers and dispatchers can list services.
- Trigger: `python manage.py sync_timetables --provider mock|csv|http` and the Sync page.

**Tests added or updated:**

- Idempotent mock import; CSV success and invalid-row failure; unknown station does not delete existing services
- HTTPX mock transport success, 401/400 not retried, 503 retried, 500 does not corrupt existing rows
- Naive datetimes rejected; HTTP provider requires a configured URL
- Viewer/dispatcher 403 on sync; administrator HTML sync; CSRF on sync POST
- Unique constraints; overnight delay; missing actuals; management command

**Commands executed and results:**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `uv run mypy` | Success: no issues found in 112 source files |
| `uv run bandit -r apps config scripts -x tests,apps/accounts/tests,apps/infrastructure/tests,apps/timetables/tests,apps/integrations/tests` | No issues identified |
| `uv run python manage.py check` | `gis.W001` only (GDAL 3.8.4) |
| `uv run python manage.py makemigrations --check --dry-run` | No changes detected |
| `uv run pytest` | **126 passed** |

## Acceptance criteria (Phase 5)

| Criterion | Status |
|---|---|
| Timetable records can be imported | **Implemented and tested** |
| Duplicate imports do not create duplicates | **Implemented and tested** |
| Invalid records are rejected or safely reported | **Implemented and tested** |
| External failures do not corrupt existing data | **Implemented and tested** |
| Synchronization results are visible | **Implemented and tested** |
| Mock provider supports deterministic local development | **Implemented and tested** |

## Phase 6 — REST API

**Objective:** Django REST Framework v1 for stations, incidents, and train services, with session authentication, Django model permissions, pagination, filtering, OpenAPI, and consistent JSON errors. Analytics and report endpoints are deferred.

**Files affected (created or updated):**

- `config/api/` — authentication (401 `WWW-Authenticate: Session`), exception handler, pagination, permission factory, router, schema/docs
- `apps/infrastructure/api/` — `StationViewSet` list/retrieve/create/patch; lat/lon floats, no WKT
- `apps/incidents/api/` — `IncidentViewSet` list/retrieve/create/patch plus `POST …/transition/`
- `apps/timetables/api/` — read-only train services and nested stops
- `apps/accounts/middleware.py` — HTML `LoginRequiredMiddleware` skips `/api/`
- `config/settings/base.py` — DRF, django-filter, drf-spectacular
- `config/urls.py` — `path("api/", include("config.api.urls"))`
- `tests/integration/test_api.py` — auth, permissions, validation, pagination, CSRF, OpenAPI
- `docs/api.md`, `docs/architecture.md`, `docs/security.md`, `README.md`, `pyproject.toml`, `uv.lock`

**Implementation details:**

- Base path `/api/v1/`. Schema `/api/schema/`, Swagger `/api/docs/` (authenticated).
- Session cookie authentication only. Unauthenticated API calls return 401 JSON, not a login redirect. Missing permission is 403. CSRF applies to unsafe methods.
- Permissions use Django model perms via `require_django_perm`, not group-name checks. Writes go through existing services (`create_station`, `create_incident`, `transition_incident`, …). Incident `status` is not writable on PATCH; use the transition action.
- Pagination: page size 20, max 100. Station search `q`/`search`; `is_active` filter. Incident filters: status, severity, category, station. Service filters: date, origin, destination, train number.
- Invalid payloads return 400. Unhandled exceptions return 500 with a generic body and are logged. Geographic coordinates are lat/lon floats with range validation.

**Tests added or updated:**

- Unauthenticated `/api/v1/stations/` and `/api/schema/` return 401 (not 302)
- Viewer GET stations/incidents/services; POST stations 403; POST incidents 201
- Dispatcher POST stations 403; administrator POST stations 201
- Invalid coordinates 400; invalid incident transition 400; valid transition 200
- Pagination of 21 stations; timetable GET 200 and POST 405
- CSRF POST without token 403; OpenAPI schema requires authentication

**Commands executed and results:**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `uv run mypy` | Success: no issues found in 149 source files |
| `uv run bandit -r apps config scripts -x tests,apps/accounts/tests,apps/infrastructure/tests,apps/incidents/tests,apps/timetables/tests,apps/integrations/tests` | No issues identified |
| `uv run python manage.py check` | `gis.W001` only (GDAL 3.8.4) |
| `uv run pytest` | **167 passed** |

## Acceptance criteria (Phase 6)

| Criterion | Status |
|---|---|
| Required station, incident, and timetable endpoints work | **Implemented and tested** |
| API permissions match user roles | **Implemented and tested** |
| Invalid requests return meaningful errors | **Implemented and tested** |
| API documentation is available | **Implemented and tested** (authenticated OpenAPI) |
| No database internals or stack traces are exposed | **Implemented and tested** |
| Analytics and report endpoints | **Not in Phase 6** (Phase 7 and 9) |

## Phase 6 follow-up — Bugbot findings

**Status:** Implemented on this branch.

| Finding | Fix |
|---|---|
| High — incident create/update then assign used separate transactions | `perform_create` and `perform_update` wrap both service calls in `transaction.atomic()`. Failed assignment (inactive user) rolls back the incident write. Tests cover create and PATCH. |

## Remaining phases

| Phase | Name | Status |
|---|---|---|
| 0 | Inspection and planning | Complete |
| 1 | Project foundation | **Complete** |
| 2 | Authentication and permissions | **Complete** |
| 3 | Railway infrastructure | **Complete** |
| 4 | Incident management | **Complete** |
| 5 | Timetable and external integration | **Complete** |
| 6 | REST API | **Complete** (this branch; not required for Phase 7) |
| 7 | Analytics | Not started |
| 8 | Dashboard and frontend | Not started |
| 9 | PDF reporting | Not started |
| 10 | Geospatial queries and map | Not started |
| 11 | Production readiness | Not started |
| 12 | Final verification | Not started |
