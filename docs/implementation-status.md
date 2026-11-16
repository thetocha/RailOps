# Implementation status

**Updated:** 2026-11-16  
**Current phase:** Phase 11 production readiness rebasing onto merged Phase 10. REST API remains Phase 6 (separate PR). Dashboard chrome remains Phase 8. PDF reports remain Phase 9.

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

## Phase 7 — Analytics

**Objective:** Date-bounded incident and delay analytics with ORM reads, Pandas transformations, typed metrics, and an HTML overview. REST `/api/v1/analytics/` waits for Phase 6.

**Files affected (created or updated):**

- `apps/analytics/` — permission carrier, period validation, queries, Pandas metrics, services, HTML overview
- `apps/analytics/migrations/0001_initial_operational_analytics.py` — unmanaged model for `view_operationalanalytics`
- `templates/analytics/overview.html`, `templates/base.html`, `templates/dashboard/home.html`
- `config/settings/base.py`, `config/urls.py`, `.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`
- `docs/architecture.md`, `docs/security.md`, `docs/decisions/ADR-005-analytics-pandas.md`, `README.md`

**Implementation details:**

- Filter at the database (incident `reported_at` window, train `service_date` inclusive). Max period **366** days. Default last **30** days.
- Pandas computes medians, monthly volume, per-station counts, and on-time percentage after the bounded fetch. ORM `COUNT` is used for total train services and optional status totals.
- Typed dataclasses (`IncidentMetrics`, `DelayMetrics`, `OverviewMetrics`) are returned to views. Raw DataFrames stay inside `metrics.py`.
- On-time threshold is **300 seconds**. Missing actual times are excluded from delay statistics, never treated as zero delay or as on time. Arrival delay is preferred when both arrival and departure exist.
- Unresolved incidents are excluded from average/median resolution time. Negative or unparsable resolution intervals are ignored.
- All three roles receive `analytics.view_operationalanalytics`. Authorization uses Django permissions, not group names.

**Tests added or updated:**

- Empty datasets; unresolved incidents; invalid/negative resolution timestamps
- Delay on-time math; unmeasured services not counted on time; outlier delays; arrival preferred over departure
- Period start after end; period longer than 366 days; half-open datetime bounds
- Overview reads persisted rows and ignores other periods; HTML empty state; invalid GET period; 403 without permission

**Commands executed and results:**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `uv run mypy` | Success: no issues found in 154 source files |
| `uv run bandit -r apps config scripts -x tests,apps/accounts/tests,apps/infrastructure/tests,apps/incidents/tests,apps/timetables/tests,apps/integrations/tests,apps/analytics/tests` | No issues identified |
| `uv run python manage.py check` | `gis.W001` only (GDAL 3.8.4) |
| `uv run pytest` | **177 passed** |

## Acceptance criteria (Phase 7)

| Criterion | Status |
|---|---|
| Analytics use real database data | **Implemented and tested** |
| Empty datasets are handled | **Implemented and tested** |
| Null values are handled correctly | **Implemented and tested** |
| Delay metrics are mathematically consistent | **Implemented and tested** |
| Expensive operations are bounded | **Implemented and tested** (max 366 days) |
| REST analytics endpoints | **Not in this PR** (Phase 6 not merged; HTML `/analytics/` is the Phase 7 surface) |

## Phase 7 follow-up — Bugbot findings

**Status:** Implemented on this branch.

| Finding | Fix |
|---|---|
| Medium — any GET query string bound the period form | Bind `AnalyticsPeriodForm` only when `period_start` or `period_end` is present. Unrelated params (e.g. `utm_source`) still load the default 30-day overview. |

## Phase 10 — Geospatial functionality

**Objective:** PostGIS nearby and nearest station queries, incident radius filtering, operations map with Leaflet, spatial tests, and documentation. Do not mix unmerged dashboard (Phase 8) or PDF (Phase 9) work.

**Files affected (created or updated):**

- `apps/infrastructure/spatial.py` — `ST_DWithin` / `ST_Distance`, radius validation, distance labels
- `apps/infrastructure/forms.py` — `NearbySearchForm`
- `apps/infrastructure/views.py` — nearby search, station detail nearest + marker payload
- `apps/infrastructure/urls.py` — `/stations/nearby/`
- `apps/incidents/spatial.py` — incidents within radius, active map incidents
- `apps/incidents/map.py` — operations map snapshot (infrastructure does not import incidents)
- `apps/incidents/map_views.py` — `/map/`
- `apps/incidents/urls.py`
- `templates/base.html`, `templates/infrastructure/`, `templates/incidents/operations_map.html`
- `static/js/operations-map.js`, `static/css/app.css`
- `apps/infrastructure/tests/test_spatial.py`, `test_nearby_views.py`
- `apps/incidents/tests/test_spatial.py`, `test_map_views.py`
- `docs/`, `README.md`

**Implementation details:**

- Station `location` remains geography SRID 4326 with the Phase 3 GIST index. Nearby uses `location__dwithin=(origin, D(m=radius))`. Nearest uses `Distance()`. Application code does not compute haversine.
- Radius 1–500_000 m (default 50_000). Nearby capped at 50 stations. Unfiltered map capped at 200 stations and 200 open/in-progress incidents at active stations.
- Nearby and map forms bind only when `latitude`, `longitude`, or `radius_meters` is present.
- `/stations/nearby/` and `/map/` require `infrastructure.view_station`. Incident markers require `incidents.view_incident`.
- Leaflet 1.9.4; OSM tiles labelled demo-only; popups use DOM `textContent`, not `innerHTML`.

**Tests added or updated:**

- Generated SQL contains `ST_DWithin` and `ST_Distance`
- Berlin 50 km includes Potsdam, excludes Hamburg; inactive stations excluded
- Nearest other station from Berlin is Potsdam; empty set returns `None`
- Invalid radius and non-4326 origin rejected
- Nearby HTML lists Potsdam, omits Hamburg; unrelated query string does not bind the form
- Operations map shows incident markers; radius filter hides Hamburg; 403 without `view_station`; station-only user sees no incident markers

**Commands executed and results:**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `uv run mypy` | Success: no issues found in 162 source files |
| `uv run bandit -r apps config scripts -x tests,apps/accounts/tests,apps/infrastructure/tests,apps/incidents/tests,apps/timetables/tests,apps/integrations/tests,apps/analytics/tests` | No issues identified |
| `uv run python manage.py check` | `gis.W001` only (GDAL 3.8.4) |
| `uv run python manage.py makemigrations --check --dry-run` | No changes detected |
| `uv run pytest` | **200 passed** |

## Acceptance criteria (Phase 10)

| Criterion | Status |
|---|---|
| Spatial queries execute against PostGIS | **Implemented** (SQL assertions for `ST_DWithin` / `ST_Distance`) |
| Coordinates are validated | **Implemented** (lat/lon bounds, radius, SRID 4326) |
| Spatial indexes are present | **Implemented and tested** (Phase 3 GIST index) |
| Map data comes from the database | **Implemented** (station and incident querysets, not hardcoded pins) |

## Phase 11 — Production readiness

**Objective:** Multi-stage production image, non-root Gunicorn process, Nginx reverse proxy, dedicated migrate/collectstatic release step, backups, deploy documentation, CI image smoke.

**Files affected (created or updated):**

- `Dockerfile` — builder (`uv sync --frozen --no-dev`) + runtime (GDAL, `USER railops`, `HEALTHCHECK`, Gunicorn `CMD`)
- `config/gunicorn.conf.py`, `config/settings/staticbuild.py`
- `scripts/release.py`, `scripts/backup_database.sh`
- `compose.production.yaml`, `deploy/nginx/default.conf`
- `.github/workflows/ci.yml` (image smoke), `.github/workflows/deploy.yml` (GHCR push after CI on `main`)
- `.dockerignore`, `.env.example`
- `tests/test_production_packaging.py`, `tests/test_release.py`, `tests/test_settings.py`
- `docs/deployment-guide.md`, `docs/security.md`, `docs/architecture.md`, `README.md`

**Implementation details:**

- Production `CMD` is Gunicorn only. `scripts/release.py` waits for PostgreSQL, runs `migrate`, then `collectstatic`. Compose `app` depends on `release` completing successfully.
- Collectstatic during the image build uses `config.settings.staticbuild` so production `SECRET_KEY` / `DB_PASSWORD` are not `ENV` defaults in the image.
- Nginx serves `/static/` and proxies `/health/` and application routes. `/media/` is not aliased.
- Backups: `pg_dump --no-password` inside the `db` container; password is not on argv.
- Deploy workflow pushes `ghcr.io/<owner>/RailOps:<sha>` after CI on `main`. It does not SSH to a VPS and does not claim zero downtime.

**Commands executed and results:**

| Command | Result |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | All checks passed |
| `uv run mypy` | Success: no issues found in 160 source files |
| `uv run bandit -r apps config scripts -x tests,apps/accounts/tests,apps/infrastructure/tests,apps/incidents/tests,apps/timetables/tests,apps/integrations/tests,apps/analytics/tests` | No issues identified |
| `uv run python manage.py check` | `gis.W001` only (GDAL 3.8.4) |
| `uv run pytest` | **186 passed** (Phase 10 tests add to this on the rebased branch) |
| `docker build -t railops:phase11 .` | **CI image-smoke** — no Docker CLI on the original agent host. CI builds the image and asserts UID ≠ 0, Gunicorn `--check-config`, and collected `app.css`. |

## Acceptance criteria (Phase 11)

| Criterion | Status |
|---|---|
| Application builds successfully | **Implemented** (CI image-smoke) |
| Application runs as non-root | **Implemented** (`USER railops`, UID asserted in CI) |
| Production settings are secure | **Implemented and tested** (Phase 1 guards + packaging tests) |
| Deployment is reproducible | **Implemented** (`compose.production.yaml` + pinned images) |
| Smoke tests pass | **CI image-smoke** |
| Rollback procedure is documented | **Implemented** (`docs/deployment-guide.md`; not zero-downtime) |

## Remaining phases

| Phase | Name | Status |
|---|---|---|
| 0 | Inspection and planning | Complete |
| 1 | Project foundation | **Complete** |
| 2 | Authentication and permissions | **Complete** |
| 3 | Railway infrastructure | **Complete** |
| 4 | Incident management | **Complete** |
| 5 | Timetable and external integration | **Complete** |
| 6 | REST API | Separate unmerged PR |
| 7 | Analytics | **Complete** |
| 8 | Dashboard and frontend | Separate unmerged PR |
| 9 | PDF reporting | Separate unmerged PR |
| 10 | Geospatial queries and map | **Complete** (merged to main) |
| 11 | Production readiness | **Complete** (this branch) |
| 12 | Final verification | Not started |
