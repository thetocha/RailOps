# Security (planning)

**Status:** Phase 5. Authentication, infrastructure, and timetable-sync authorization are implemented; later controls remain requirements.

- Django password hashing; CSRF; session cookies `Secure`/`HttpOnly` in production; `ALLOWED_HOSTS`; CSRF trusted origins.
- Groups: Administrator / Dispatcher / Viewer. Views check Django permissions, not group names.
- Station and railway-line writes require `add_*` / `change_*` model permissions (Administrator). Viewers and dispatchers receive `view_*` only. `delete_*` is not granted; the UI deactivates instead of deleting.
- Timetable HTML writes go through `integrations.run_timetable_sync` (Administrator). Viewers and dispatchers may list train services only. Django admin for services and sync runs is superuser and read-only.
- Provider payloads are validated with Pydantic before persistence. CSV rows that fail validation are skipped and recorded on `ExternalSyncRun.error_summary`. Datetimes must be timezone-aware. CSV uploads are limited to 1 MB and `.csv` names.
- HTTPX retries transport errors and selected transient statuses, respects `Retry-After`, and does not retry 4xx. Tests use `httpx.MockTransport`; CI does not call the public internet.
- Coordinates are validated (latitude −90..90, longitude −180..180) before a SRID 4326 point is stored.
- Secrets only in environment; `.env.example` placeholders. `EXTERNAL_RAILWAY_API_KEY` is sent as a Bearer header and is not logged.
- Validate all inputs including CSV, coordinates, report ranges.
- Do not log passwords, tokens, API keys, cookies, or full provider payloads.
- Report files: authorised download only; no path traversal.
- Dedicated DB user, not superuser, in production.
- Bandit + pip-audit in CI; do not disable security to pass tests.
