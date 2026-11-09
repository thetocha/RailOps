# ADR-006: PDF generation and storage

**Status:** Accepted (Phase 0)  
**Date:** 2026-11-09

## Context

Monthly operations PDF via WeasyPrint. WeasyPrint needs native libraries (Pango/Cairo); this is awkward on Windows. Files must not live in git or in PostgreSQL.

## Options considered

1. WeasyPrint HTML→PDF (specified).  
2. ReportLab canvas API (more code, less HTML reuse).  
3. External paid PDF API (unnecessary dependency).

## Decision

WeasyPrint from Django templates. Store via `FileField` on configurable storage (`MEDIA_ROOT` locally). Synchronous generation for MVP if the period is bounded. Document that large jobs would become a background worker later (no Celery until needed). Prefer generating PDFs **inside Linux Docker** if native Windows deps fail — that is an environment choice, not a product change.

## Consequences

- Phase 9 needs a template + CSS subset safe for print.  
- Download view authorises then streams; no open directory listing.  
- Native WeasyPrint on the current Windows host is **unverified**.

## Trade-offs

Good-looking HTML reports vs native library burden on developer machines.
