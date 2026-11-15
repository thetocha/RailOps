# Testing strategy

**Status:** Phase 5. Foundation, auth, infrastructure, incident, delay calculation, and timetable-sync tests exist.

## Stack

pytest, pytest-django, factory_boy if model graphs need it. Test settings use **PostgreSQL/PostGIS**, not SQLite.

## Layers (from Phase 2 onward)

| Kind | Examples |
|---|---|
| Unit | Incident transitions, delay seconds, analytics pure functions, date-range validation, provider payload schemas |
| Model | Unique constraints, spatial field, check constraints |
| API | Status codes, authn/authz, pagination, error shape |
| Integration | Incident+history transaction, idempotent import, failed HTTP (mocked), PDF generate, DWithin/nearest |
| Security | Viewer cannot POST incidents; dispatcher cannot manage users; CSRF; download ACL |

External HTTP is always mocked. Coverage goal: ≥ 80% of business logic, not vanity lines.
