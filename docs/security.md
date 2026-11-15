# Security (planning)

**Status:** Phase 9. Authentication, infrastructure, incident, timetable-sync, analytics, and report download authorization are implemented; REST API remains a later phase.

- Django password hashing; CSRF; session cookies `Secure`/`HttpOnly` in production; `ALLOWED_HOSTS`; CSRF trusted origins.
- Groups: Administrator / Dispatcher / Viewer. Views check Django permissions, not group names.
- Station and railway-line writes require `add_*` / `change_*` model permissions (Administrator). Viewers and dispatchers receive `view_*` only. `delete_*` is not granted; the UI deactivates instead of deleting.
- Incidents: Dispatcher and Administrator may create/update/assign/transition. Viewer is read-only. Closed incidents can be reopened only with `incidents.reopen_closed_incident` (Administrator). Incident events are immutable.
- Timetable HTML writes go through `integrations.run_timetable_sync` (Administrator). Viewers and dispatchers may list train services only. Django admin for services and sync runs is superuser and read-only.
- Analytics HTML (`/analytics/`) requires `analytics.view_operationalanalytics` (Administrator, Dispatcher, Viewer). Date ranges are validated (start ≤ end, max 366 days) before any query runs.
- Reports HTML (`/reports/`) requires `reports.view_report` and `reports.add_report` (Administrator only). Monthly periods are validated (start ≤ end, max 31 days) before a row is created. Downloads re-check `view_report`, require `status=success` and a stored file, and stream through the authorised view. `upload_to` ignores caller filenames and writes `reports/<uuid>.pdf` under `MEDIA_ROOT`. WeasyPrint rejects remote URLs. Failed generation stores a generic error summary, not exception text. REST `/api/v1/reports/` waits for Phase 6.
- Provider payloads are validated with Pydantic before persistence. CSV rows that fail validation are skipped and recorded on `ExternalSyncRun.error_summary`. Datetimes must be timezone-aware. CSV uploads are limited to 1 MB and `.csv` names.
- HTTPX retries transport errors and selected transient statuses, respects `Retry-After`, and does not retry 4xx. Tests use `httpx.MockTransport`; CI does not call the public internet.
- Coordinates are validated (latitude −90..90, longitude −180..180) before a SRID 4326 point is stored.
- Secrets only in environment; `.env.example` placeholders. `EXTERNAL_RAILWAY_API_KEY` is sent as a Bearer header and is not logged.
- Validate all inputs including CSV, coordinates, report ranges.
- Do not log passwords, tokens, API keys, cookies, or full provider payloads.
- Report files: authorised download only; no path traversal. WeasyPrint is pinned at 70.0 for SSRF/url_fetcher and image-pipeline fixes. HTML is Django-escaped analytics output, not untrusted markup. `presentational_hints` is left off (CVE-2026-49452 only applies when it is enabled).
- Dedicated DB user, not superuser, in production.
- Bandit + pip-audit in CI; do not disable security to pass tests.
