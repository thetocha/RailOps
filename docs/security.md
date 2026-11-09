# Security (planning)

**Status:** Phase 0. Controls below are requirements, not implemented.

- Django password hashing; CSRF; session cookies `Secure`/`HttpOnly` in production; `ALLOWED_HOSTS`; CSRF trusted origins.  
- Groups: Administrator / Dispatcher / Viewer; tests for each.  
- Secrets only in environment; `.env.example` placeholders.  
- Validate all inputs including CSV, coordinates, report ranges.  
- Do not log passwords, tokens, API keys, cookies, or full provider payloads.  
- Report files: authorised download only; no path traversal.  
- Dedicated DB user, not superuser, in production.  
- Bandit + pip-audit in CI; do not disable security to pass tests.
