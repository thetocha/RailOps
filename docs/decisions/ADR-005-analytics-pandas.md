# ADR-005: Analytics and Pandas

**Status:** Accepted (Phase 0)  
**Date:** 2026-11-09

## Context

The role asks for Pandas in reporting, while PostgreSQL is better for simple aggregations. Unbounded `DataFrame` loads are a reliability risk.

## Options considered

1. Pandas for every dashboard number (rejected).  
2. SQL/ORM only (weaker Pandas demonstration).  
3. **SQL filter/aggregate first, Pandas for bounded multi-metric reports.**

## Decision

ORM/SQL for routine dashboard counts. Pandas for monthly report composition, medians, and multi-source frames **after** a date-bounded query. Return typed dataclasses/Pydantic models to views. On-time = delay ≤ 300 seconds; missing actuals excluded.

## Consequences

- Tests can feed lists of dicts into pure functions without Django.  
- Must enforce max reporting window to bound memory.

## Trade-offs

Slightly more plumbing vs a single “dump table to Pandas” anti-pattern.
