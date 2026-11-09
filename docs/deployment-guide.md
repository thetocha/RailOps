# Deployment guide

**Status:** Phase 0 planning. Nothing is deployed.

## Target (Phase 11)

Multi-stage Dockerfile, non-root, pinned base image, Gunicorn, Nginx or equivalent, separate migrate job, health endpoint, env-based secrets. No `runserver` in production. No migrate-on-worker-start.

Rollback: keep previous image; document it honestly (not “zero downtime” unless the host actually supports it).

CI (planned): GitHub Actions — lint, typecheck, Bandit, pip-audit, tests on PostGIS, then image build on main.
