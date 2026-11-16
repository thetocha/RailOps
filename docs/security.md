# Security (planning)

**Status:** Phase 10. Authentication, infrastructure, incident, timetable-sync, analytics, and geospatial authorization are implemented; REST API and report download controls remain later phases.

- Django password hashing; CSRF; session cookies `Secure`/`HttpOnly` in production; `ALLOWED_HOSTS`; CSRF trusted origins.
- Groups: Administrator / Dispatcher / Viewer. Views check Django permissions, not group names.
- Station and railway-line writes require `add_*` / `change_*` model permissions (Administrator). Viewers and dispatchers receive `view_*` only. `delete_*` is not granted; the UI deactivates instead of deleting.
- Incidents: Dispatcher and Administrator may create/update/assign/transition. Viewer is read-only. Closed incidents can be reopened only with `incidents.reopen_closed_incident` (Administrator). Incident events are immutable.
- Timetable HTML writes go through `integrations.run_timetable_sync` (Administrator). Viewers and dispatchers may list train services only. Django admin for services and sync runs is superuser and read-only.
- Analytics HTML (`/analytics/`) requires `analytics.view_operationalanalytics` (Administrator, Dispatcher, Viewer). Date ranges are validated (start ≤ end, max 366 days) before any query runs.
- Provider payloads are validated with Pydantic before persistence. CSV rows that fail validation are skipped and recorded on `ExternalSyncRun.error_summary`. Datetimes must be timezone-aware. CSV uploads are limited to 1 MB and `.csv` names.
- HTTPX retries transport errors and selected transient statuses, respects `Retry-After`, and does not retry 4xx. Tests use `httpx.MockTransport`; CI does not call the public internet.
- Coordinates are validated (latitude −90..90, longitude −180..180) before a SRID 4326 point is stored. Nearby and map radius is 1–500_000 metres. Origins that are not SRID 4326 are rejected.
- `/stations/nearby/` and `/map/` require `infrastructure.view_station`. Incident markers on the map are included only when the user also has `incidents.view_incident`. Map popups are built from DOM nodes, not `innerHTML`.
- OpenStreetMap tiles on `/map/` and station pages are for local demonstration only; they are not a production tile-usage agreement.
- Secrets only in environment; `.env.example` placeholders. `EXTERNAL_RAILWAY_API_KEY` is sent as a Bearer header and is not logged.
- Validate all inputs including CSV, coordinates, report ranges.
- Do not log passwords, tokens, API keys, cookies, or full provider payloads.
- Report files: authorised download only; no path traversal.
- Dedicated DB user, not superuser, in production.
- Bandit + pip-audit in CI; do not disable security to pass tests.
