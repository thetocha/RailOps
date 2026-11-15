# Security (planning)

**Status:** Phase 3. Authentication and infrastructure authorization are implemented; later controls remain requirements.

- Django password hashing; CSRF; session cookies `Secure`/`HttpOnly` in production; `ALLOWED_HOSTS`; CSRF trusted origins.
- Groups: Administrator / Dispatcher / Viewer. Views check Django permissions, not group names.
- Station and railway-line writes require `add_*` / `change_*` model permissions (Administrator). Viewers and dispatchers receive `view_*` only. `delete_*` is not granted; the UI deactivates instead of deleting.
- Coordinates are validated (latitude −90..90, longitude −180..180) before a SRID 4326 point is stored.
- Secrets only in environment; `.env.example` placeholders.
- Validate all inputs including CSV, coordinates, report ranges.
- Do not log passwords, tokens, API keys, cookies, or full provider payloads.
- Report files: authorised download only; no path traversal.
- Dedicated DB user, not superuser, in production.
- Bandit + pip-audit in CI; do not disable security to pass tests.
