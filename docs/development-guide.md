# Development guide

**Status:** Phase 2. Commands below were run on 2026-11-09.

## Prerequisites

| Tool | Version used |
|---|---|
| Python | 3.13.14 (`python`; Windows `py` launcher is absent) |
| uv | 0.12.7 |
| Docker / Compose | 29.7.2 / v5.4.0 |

Native GDAL/GEOS are **not** present on this Windows host. GeoDjango (and therefore `manage.py`, pytest, and mypy with the Django plugin) must run **inside Docker**. Ruff, Bandit, and pip-audit run on the host.

## First-time setup

```powershell
copy .env.example .env
uv sync --all-groups
docker compose up -d --build
docker compose exec app python manage.py migrate
```

If host ports **5432** or **8000** are already taken (common when another Postgres/Django stack is running), set in `.env`:

```dotenv
DB_PUBLISH_PORT=5433
APP_PUBLISH_PORT=8001
CSRF_TRUSTED_ORIGINS=http://localhost:8001,http://127.0.0.1:8001
```

Inside the Compose network the database still listens on 5432 (`DB_HOST=db`). `DB_PORT` is the container port, not the host publish port.

Health:

```powershell
curl http://127.0.0.1:8000/health/
# or :8001 if APP_PUBLISH_PORT=8001
```

Expected: `{"status":"ok"}`.

## First administrator and login

Migrate (also seeds the three role groups via accounts `post_migrate`):

```powershell
docker compose exec app python manage.py migrate
```

Create the first account (Django superuser — has all permissions even without a group):

```powershell
docker compose exec app python manage.py createsuperuser
```

Optionally attach that superuser to the Administrator group (so the Users UI shows the role):

```powershell
docker compose exec app python manage.py seed_role_groups --assign-superusers
```

`seed_role_groups` is idempotent and safe to re-run. Groups are also created automatically after migrate. The command only adds/removes permissions on `accounts.user`; later apps can attach their own permissions to the same groups.

Open (port **8001** on this workstation):

```text
http://127.0.0.1:8001/accounts/login/
```

After login you land on `/` (dashboard). Administrators see **Users** (`/accounts/users/`) — list, create, edit, deactivate, assign role groups. Dispatchers and viewers can change their own password but receive HTTP 403 on user management.

Password reset: `/accounts/password-reset/`. In development the email is printed to the **app container log** (`docker compose logs app`). Production settings send via SMTP (`MAILERS` + `EMAIL_HOST*` env vars in `.env.example`). Django 6 uses `MAILERS` only — do not also set `EMAIL_BACKEND` as a Django setting.

Logout is POST (button in the nav) so CSRF applies.

## Tests

Always PostGIS. Never SQLite. Compose sets `DJANGO_SETTINGS_MODULE` to development for runserver, so override it for pytest:

```powershell
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test -e SECRET_KEY=test-insecure-secret-key-for-automated-tests-only app pytest
```

## Quality

Host (no GDAL required):

```powershell
uv run ruff check .
uv run ruff format --check .
uv run bandit -r apps config scripts -x tests,apps/accounts/tests
uv run pip-audit
```

Docker (GDAL required):

```powershell
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test -e SECRET_KEY=test-insecure-secret-key-for-automated-tests-only app mypy
docker compose exec app python manage.py check
```

## Native Django (Linux/macOS with GDAL)

```powershell
docker compose up -d db
# keep DB_HOST=localhost and DB_PORT matching DB_PUBLISH_PORT
uv run python manage.py migrate
uv run python manage.py runserver
uv run pytest
uv run mypy
```

This path is **blocked on the Phase 1 Windows workstation** (`gdalinfo` not found, `find_library("gdal")` is `None`).
