# Implementation status

**Updated:** 2026-11-09  
**Current phase:** Phase 2 complete. Phases 3–12 not started.

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

**Remaining limitations:**

- Stations, lines, incidents, DRF, analytics, PDF, and map UI are **not** implemented (Phase 3+).
- `accounts.view_operations` / `accounts.change_operations` exist for later apps; there are no operational records yet.
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

## Phases 3–12 — not started

| Phase | Name | Status |
|---|---|---|
| 0 | Inspection and planning | Complete |
| 1 | Project foundation | **Complete** |
| 2 | Authentication and permissions | **Complete** |
| 3 | Railway infrastructure | Not started |
| 4 | Incident management | Not started |
| 5 | Timetable and external integration | Not started |
| 6 | REST API | Not started |
| 7 | Analytics | Not started |
| 8 | Dashboard and frontend | Not started |
| 9 | PDF reporting | Not started |
| 10 | Geospatial queries and map | Not started |
| 11 | Production readiness | Not started |
| 12 | Final verification | Not started |
