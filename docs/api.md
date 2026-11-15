# REST API (planning)

**Status:** Phase 0 for REST. HTML analytics exists in Phase 7 at `/analytics/`. REST `/api/v1/` is Phase 6.

Base path: `/api/v1/`. Django REST Framework, OpenAPI via drf-spectacular, session authentication for the browser MVP.

Planned resources (spec §7.1): stations, incidents (+ `transition`), train services and stops, analytics overview/incidents/delays, reports (+ download). Analytics **HTML** is at `/analytics/`. Reports **HTML** is at `/reports/` (Administrator generate/download). Analytics and reports **JSON** endpoints wait for the Phase 6 API package.

Permissions match roles (Viewer GET; Dispatcher incident writes; Administrator full). Hiding UI is not enforcement. Error bodies must not include stack traces or schema internals.
