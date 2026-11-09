# REST API (planning)

**Status:** Phase 0. No endpoints exist.

Base path: `/api/v1/`. Django REST Framework, OpenAPI via drf-spectacular, session authentication for the browser MVP.

Planned resources (spec §7.1): stations, incidents (+ `transition`), train services and stops, analytics overview/incidents/delays, reports (+ download).

Permissions match roles (Viewer GET; Dispatcher incident writes; Administrator full). Hiding UI is not enforcement. Error bodies must not include stack traces or schema internals.
