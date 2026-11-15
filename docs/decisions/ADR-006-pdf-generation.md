# ADR-006: PDF generation and storage

**Status:** Implemented (Phase 9)  
**Date:** 2026-11-15

## Context

Monthly operations PDF via WeasyPrint. WeasyPrint needs native libraries (Pango/Cairo); this is awkward on Windows. Files must not live in git or in PostgreSQL.

## Options considered

1. WeasyPrint HTML→PDF (specified).  
2. ReportLab canvas API (more code, less HTML reuse).  
3. External paid PDF API (unnecessary dependency).

## Decision

WeasyPrint from Django templates. Store via `FileField` on configurable storage (`MEDIA_ROOT` locally). Synchronous generation for MVP if the period is bounded. Document that large jobs would become a background worker later (no Celery until needed). Prefer generating PDFs **inside Linux Docker** if native Windows deps fail — that is an environment choice, not a product change.

## Consequences

- Monthly HTML template + print CSS live in `templates/reports/monthly_operations.html` and `apps/reports/static/monthly_operations.css`. WeasyPrint is given local strings and a blocked URL fetcher.
- Download view authorises then streams; `/media/` is not served. Files sit under `MEDIA_ROOT/reports/<uuid>.pdf`.
- Generation is synchronous and capped at 31 days. Larger jobs would need a background worker (not Celery in this MVP).
- Native WeasyPrint on Windows remains **unverified**; CI and the Linux image install Pango/Cairo/GdkPixbuf and DejaVu fonts.

## Trade-offs

Good-looking HTML reports vs native library burden on developer machines.
