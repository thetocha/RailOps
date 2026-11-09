# ADR-001: Modular monolith

**Status:** Accepted (Phase 0)  
**Date:** 2026-11-09

## Context

RailOps must demonstrate production-quality Django engineering for an interview-style MVP: several domains (accounts, infrastructure, incidents, timetables, integrations, analytics, reports), one team, one deployable artefact. The specification forbids microservices.

## Options considered

1. **Modular Django monolith** — one project, multiple apps, one database.  
2. **Microservices** — separate deployables per domain.  
3. **Layered single app** — all models in one Django app.

## Decision

Use a **modular monolith**: Django apps aligned to business capabilities, shared PostgreSQL/PostGIS, in-process service calls.

## Consequences

- Shared transactions for incident + history, and for timetable upserts.  
- Single permission model (Groups).  
- Independent deploy/scale per module is not available (acceptable for MVP).  
- App boundaries and import direction must be documented and reviewed in code review.

## Trade-offs

| Gain | Cost |
|---|---|
| Simplicity, ACID, one CI pipeline | Cannot scale timetable sync separately |
| Fast feature delivery | Discipline required to avoid a “ball of mud” |
| Matches Django strengths | Not a distributed-systems showcase |
