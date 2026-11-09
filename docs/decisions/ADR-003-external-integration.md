# ADR-003: External integration adapter

**Status:** Accepted (Phase 0)  
**Date:** 2026-11-09

## Context

Phase 5 must import timetables from an “external provider” using production-style HTTP (timeouts, retries, validation, idempotent sync) **without inventing a fake official railway API** or scraping unofficial endpoints.

High-level market scan (planning, not an integration):

- **Operator/national APIs** (examples: GB National Rail Darwin, various European RIS/timetable APIs) typically need registration, keys, and contractual terms. They are not assumed available for this repo.  
- **GTFS / NeTEx static feeds** are published by some agencies under their own licences; usable only after licence and attribution check, as a **named file/URL**, not as “the railway API”.  
- **Unofficial reverse-engineered JSON** is disallowed as a claimed production service.

## Options considered

1. HTTPX client to a specific live API now (blocked: no licensed endpoint selected).  
2. **Adapter interface + mock + CSV**, optional HTTPX client later.  
3. Direct CSV-only import with no interface (weaker demonstration of integration design).

## Decision

Define `RailwayProviderInterface`. Ship **MockRailwayProvider** (deterministic) and **CSVRailwayProvider** as the MVP sources. Implement **ExternalRailwayAPIClient** (HTTPX: timeouts, limited retry, `Retry-After`, no retry of 4xx auth) only when a concrete, documented, licensed source is configured via env (`EXTERNAL_RAILWAY_API_URL` / key). Sync is a management command; idempotent via unique `(external_id, service_date)` and stop uniqueness. `ExternalSyncRun` records outcomes without secrets or raw payloads.

Until a real source is chosen, CI uses mock/CSV only. Tests **must not** call the public internet.

## Consequences

- Demo always works offline.  
- Interview can show adapter + HTTPX design even if the live client is pointed at a mock HTTP server in tests.  
- Operators cannot claim “we are integrated with Deutsche Bahn / Network Rail” unless a real contract exists.

## Trade-offs

| Gain | Cost |
|---|---|
| Honest, testable, idempotent | Live network demo optional |
| Same persist path for all sources | CSV schema is our contract, not a national standard |
