# Deployment guide

**Status:** Phase 11. Production image, Gunicorn, Nginx, a dedicated migrate/collectstatic release step, backups, and a GitHub Actions image workflow exist. There is no managed VPS in this repository — cut-over is a documented host procedure, not an automated SSH deploy.

## What production is

```text
Internet --> Nginx (static + reverse proxy) --> Gunicorn --> Django
                                      |
                                      v
                               PostgreSQL / PostGIS
```

- The application image defaults to `config.settings.production`.
- Gunicorn is the WSGI server. Do not use `runserver` in production.
- Migrations and `collectstatic` run in the **release** Compose service (`python scripts/release.py`). Application workers do not migrate on startup.
- Nginx serves `/static/` from the shared `staticfiles` volume and proxies everything else, including `/health/` and `/media/`, to Django so `LoginRequiredMiddleware` still applies.
- OpenStreetMap tiles used by later map UI are demo-only; they are not a production tile contract.

## Build and run (small VPS)

1. Copy `.env.example` to `.env` on the host. Replace `SECRET_KEY` and `DB_PASSWORD` with strong values. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the public hostname (`https://...`). Production settings refuse `DEBUG=True`, placeholder secrets, empty hosts, and `*`.
2. Set `SECURE_SSL_REDIRECT=True` when TLS terminates in front of Nginx (or on Nginx itself). Leave it `False` only for an HTTP-only lab.
3. Build and start:

```bash
docker compose -f compose.production.yaml build
docker compose -f compose.production.yaml up -d
```

`release` waits for PostGIS, runs `migrate`, then `collectstatic` into the `staticfiles` volume. `app` starts Gunicorn only after `release` exits 0. Nginx starts after the app health check (`GET /health/` → `{"status":"ok"}`).

4. Create the first superuser (one-off, not in the worker command):

```bash
docker compose -f compose.production.yaml exec app python manage.py createsuperuser
```

5. Confirm:

```bash
curl -fsS "http://127.0.0.1:${NGINX_PUBLISH_PORT:-80}/health/"
```

## GitHub Actions

- Pull requests and pushes run `.github/workflows/ci.yml` (Ruff, mypy, Bandit, pip-audit, pytest on PostGIS, production image smoke).
- After CI succeeds on `main`, `.github/workflows/deploy.yml` rebuilds the image, repeats the non-root/Gunicorn smoke, and pushes `ghcr.io/<owner>/RailOps:<sha>` and `:main`.
- That workflow does **not** SSH to a VPS and does **not** run migrations. Pull the tagged image on the host and run the Compose release step there.

## Rollback

This topology is not zero-downtime. Keep the previous image digest.

1. Note the running tag (`docker compose -f compose.production.yaml images` or the GHCR digest you pulled).
2. Set `RAILOPS_IMAGE=ghcr.io/<owner>/RailOps:<previous-sha>`.
3. Run `docker compose -f compose.production.yaml up -d`.
4. If a migration must be reversed, that is a **separate** release command, for example `docker compose -f compose.production.yaml run --rm release python manage.py migrate app_label previous_migration`. Do not reverse migrations unless you have a tested plan and a backup. Django does not make schema rollback automatic.

## Database backups

`scripts/backup_database.sh` runs `pg_dump` **inside** the `db` container (`--no-password`, credentials not on argv) and writes a custom-format dump to `BACKUP_DIR` (default `./backups`).

```bash
chmod 700 backups
BACKUP_DIR=./backups ./scripts/backup_database.sh
```

Restore (destructive — restore onto a stopped app, after taking a fresh dump):

```bash
docker compose -f compose.production.yaml exec -T db \
  pg_restore -U railops -d railops --clean --if-exists < backups/railops-YYYYMMDDTHHMMSSZ.dump
```

Schedule the dump from cron or a systemd timer on the host (daily is enough for this MVP). Store copies off the VPS. The `railops` database role is a normal user, not a PostgreSQL superuser.

## Logging

Gunicorn and Django log to stdout/stderr. Capture with `docker compose logs`. Do not log passwords, tokens, API keys, session cookies, or full provider payloads. `/health/` is exempt from TLS redirect so probes do not 301-loop.

## Known host work

TLS certificates, a real hostname, off-box backup storage, and OSM/tile licensing are operator tasks. This repository ships a reproducible image and Compose file, not a cloud account.
