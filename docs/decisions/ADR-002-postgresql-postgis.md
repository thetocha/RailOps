# ADR-002: PostgreSQL and PostGIS

**Status:** Accepted (Phase 0)  
**Date:** 2026-11-09

## Context

Stations have coordinates; the product requires radius and nearest-station queries, GeoDjango, and spatial indexes. Analytics and incidents need relational constraints. The specification forbids SQLite as a PostGIS stand-in in integration tests.

## Options considered

1. **PostgreSQL + PostGIS + GeoDjango** (specified).  
2. SQLite + application haversine (rejected: wrong answers at scale, no spatial index, violates spec).  
3. Separate geospatial microservice (rejected: ADR-001).

## Decision

PostgreSQL with PostGIS. Station `PointField` SRID 4326 (`geography=True` for metre distances). Spatial indexes created by migrations. Docker Compose provides PostGIS for development and CI.

**Target versions (planning, pin in Phase 1 compose file):** PostgreSQL **16** or **17** with a **pinned** PostGIS image (never `latest`). Exact image tag is chosen when Phase 1 writes `compose.yaml`, after checking current `postgis/postgis` tags.

## Consequences

- Local Windows without PostGIS cannot run spatial tests; Docker is required for those tests.  
- GDAL/GEOS must be available in the Django environment (Linux container is the reliable path; native Windows GIS stack is a known friction).  
- Production needs a dedicated non-superuser DB role.

## Trade-offs

| Gain | Cost |
|---|---|
| Correct spatial queries, constraints, one store | Heavier local setup than SQLite |
| Aligns with spec and GeoDjango | Image size, GDAL deps in Docker |
