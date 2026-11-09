# ADR-004: Server-rendered frontend

**Status:** Accepted (Phase 0)  
**Date:** 2026-11-09

## Context

The UI must be a professional internal dashboard. The specification forbids React and a separate frontend build.

## Options considered

1. Django templates + Bootstrap 5 + vanilla JS (Chart.js, Leaflet).  
2. Django + HTMX-heavy SPA-like UX (optional later, not required).  
3. React/Vite SPA (out of scope).

## Decision

Server-rendered Django templates, Bootstrap 5, progressive enhancement. REST API is additional, not the HTML data layer.

## Consequences

- Forms and CSRF stay in Django.  
- Charts/maps require JS but pages remain usable without them for core CRUD.  
- No Node build in CI except if later added for nothing — keep CI Python-centric.

## Trade-offs

Faster, spec-compliant UI vs less “modern SPA” surface in interviews (acceptable; API still exists).
