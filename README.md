# RailOps

Internal railway operations and analytics platform. This repository currently contains **Phase 1 — project foundation** and **Phase 2 — authentication and permissions**: Django project layout, custom user model, PostGIS, health endpoint, session login/logout, password change/reset, role groups, administrator user management, quality tooling, Docker Compose, and CI.

Later phases (stations, incidents, API, analytics, reports) are specified in `AGENTS.md` and are **not implemented yet**.

## Technology (Phase 1)

| Component | Version |
|---|---|
| Python | 3.13.14 (`requires-python >=3.13,<3.14`) |
| Django | 6.1.3 |
| django-environ | 0.14.0 |
| psycopg | 3.3.8 (binary) |
| gunicorn | 26.2.0 |
| PostgreSQL / PostGIS | `postgis/postgis:16-3.5` |
| pytest / pytest-django | 9.2.0 / 4.14.0 |
| ruff | 0.17.4 |
| mypy / django-stubs | 1.18.2 / 6.1.2 |
| Package manager | uv 0.12.7 |

## Prerequisites

- Python 3.13 (`python` on this Windows workstation; the `py` launcher may be absent)
- [uv](https://docs.astral.sh/uv/)
- Docker with Compose (required for PostGIS and for GeoDjango on Windows)

Native Windows **does not** currently provide GDAL/GEOS. GeoDjango therefore cannot import on a bare Windows Python install. Run the application and tests **in Docker** on this host. Linux and GitHub Actions install GDAL via apt.

## Local setup (Docker — recommended)

```powershell
copy .env.example .env
docker compose up -d --build
docker compose exec app python manage.py migrate
```

If **5432** or **8000** are already in use, set `DB_PUBLISH_PORT` and `APP_PUBLISH_PORT` in `.env` (this workstation used 5433 and 8001).

Health check:

```powershell
curl http://127.0.0.1:8000/health/
```

Expected: `{"status": "ok"}`.

Login (after `migrate` + `createsuperuser`): `http://127.0.0.1:8000/accounts/login/` (or `:8001` if remapped). See `docs/development-guide.md`.

The app service uses Django's development server. Do not use that in production.

## Tests, lint, types (Docker)

```powershell
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test -e SECRET_KEY=test-insecure-secret-key-for-automated-tests-only app pytest
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test -e SECRET_KEY=test-insecure-secret-key-for-automated-tests-only app mypy
uv run ruff check .
uv run ruff format --check .
```

Tests use PostGIS (`config.settings.test`). SQLite is not used.

## uv on the host (lint without GDAL)

Host-side Python can install dependencies and run Ruff without GDAL:

```powershell
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
```

`uv run pytest`, `uv run mypy`, and `uv run python manage.py` need GDAL because settings load GeoDjango. On this Windows workstation that path is blocked until GDAL is installed; use Docker as above.

## Environment

Copy `.env.example` to `.env`. Never commit `.env`. Placeholders such as `SECRET_KEY=replace-me` are for local development only. Production settings refuse placeholder secrets, empty/`*` `ALLOWED_HOSTS`, and `DEBUG=True`.

## Project layout (Phase 2)

```text
manage.py
config/                 # Django project (settings, URLs, health)
apps/accounts/          # Custom user, roles, login, user management
templates/ static/
tests/
compose.yaml            # PostGIS + app
.github/workflows/ci.yml
```

## Known limitations

- No stations, incidents, REST API, analytics, or PDF reports yet (Phase 3+).
- Native Windows GDAL/GEOS is not installed; GeoDjango runs in Linux containers and CI.
- Production Dockerfile hardening (non-root image split, Nginx, Gunicorn process model) is Phase 11; the Phase 1 image is enough to run the app and tests.
