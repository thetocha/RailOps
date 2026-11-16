# Testing strategy

**Status:** Phase 11. Foundation, auth, infrastructure, incident, delay calculation, timetable-sync, analytics, PostGIS spatial, and production packaging tests exist.

## Stack

pytest, pytest-django, factory_boy if model graphs need it. Test settings use **PostgreSQL/PostGIS**, not SQLite.

## Layers (from Phase 2 onward)

| Kind | Examples |
|---|---|
| Unit | Incident transitions, delay seconds, analytics pure functions, date-range validation, provider payload schemas |
| Model | Unique constraints, spatial field, check constraints |
| API | Status codes, authn/authz, pagination, error shape |
| Integration | Incident+history transaction, idempotent import, failed HTTP (mocked), `ST_DWithin` / `ST_Distance`, map permission |
| Spatial | Radius bounds, inactive stations excluded, Berlin–Potsdam vs Hamburg, closed incidents omitted from the map |
| Security | Viewer cannot POST incidents; dispatcher cannot manage users; CSRF; download ACL |

External HTTP is always mocked. Coverage goal: ≥ 80% of business logic, not vanity lines.
