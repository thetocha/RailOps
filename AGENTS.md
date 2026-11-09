# RailOps — Master Implementation Specification

**Project:** Railway Operations & Analytics Platform  
**Document type:** Product Requirements + Technical Specification + Agent Implementation Instructions  
**Primary purpose:** Demonstrate production-quality Python/Django development skills and cover the technical requirements of a railway software engineering position.  
**Architecture:** Modular Django monolith  
**Development approach:** Incremental, test-driven, security-conscious  
**Target:** A deployable, documented, demonstrable MVP

---

# 1. Instructions for the coding agent

## 1.1 Your role

You are acting as a senior Python/Django engineer and technical lead responsible for designing, implementing, testing, and documenting RailOps.

You are not a code-generation assistant that simply produces files on request. You are responsible for delivering a complete working application.

You must:

1. Analyse the existing repository before making changes.
2. Design the architecture before implementing major features.
3. Break work into small, independently verifiable tasks.
4. Implement features incrementally.
5. Write automated tests alongside application code.
6. Run relevant quality checks before considering a task complete.
7. Document important technical decisions.
8. Identify technical risks and communicate them.
9. Never claim functionality is implemented unless it actually works and has been tested.
10. Avoid unnecessary complexity and dependencies.

### Engineering priorities

In order of importance:

1. Correctness and reliability.
2. Security.
3. Maintainability.
4. Testability.
5. Performance.
6. Developer experience.
7. User experience.

Do not sacrifice security or maintainability for faster implementation.

## 1.2 Coding principles

Follow these principles throughout the project.

**SOLID**
- Single Responsibility Principle.
- Open/Closed Principle.
- Liskov Substitution Principle.
- Interface Segregation Principle.
- Dependency Inversion Principle.

Apply them pragmatically. Do not create abstractions that have no real purpose.

**DRY**
- Avoid duplicated business logic.
- Extract reusable functionality when duplication is meaningful.
- Do not create generic frameworks for one-off operations.

**KISS**
- Prefer straightforward Django functionality over custom infrastructure.
- Use Django ORM rather than raw SQL unless there is a measurable reason not to.
- Use Django authentication and permission systems rather than reinventing them.

**Explicit is better than implicit**
- Use meaningful names.
- Add type annotations.
- Handle expected exceptions explicitly.
- Avoid hidden side effects.
- Avoid excessive use of global state.

**Fail safely**
- Validate all external data.
- Do not expose internal exceptions to users.
- Never silently ignore failed operations.
- Log errors with sufficient diagnostic context without exposing secrets or personal information.

## 1.3 Agent working protocol

Before implementing anything:

1. Inspect repository structure.
2. Read existing README and configuration.
3. Identify installed Python and package manager versions.
4. Check whether the project already contains implementation.
5. Identify inconsistencies between existing code and this specification.
6. Prepare an implementation plan.

Maintain these documents:

```text
docs/
├── architecture.md
├── database-design.md
├── development-guide.md
├── testing-strategy.md
├── deployment-guide.md
├── security.md
├── api.md
├── decisions/
│   ├── ADR-001-modular-monolith.md
│   ├── ADR-002-postgresql-postgis.md
│   └── ADR-003-external-integration.md
└── implementation-status.md
```

Update `implementation-status.md` after each completed milestone.

Each task must include:

- Objective.
- Files affected.
- Implementation details.
- Tests added or updated.
- Commands executed.
- Test results.
- Remaining limitations.

Do not proceed to the next major phase if the current phase has failing tests or unresolved critical security issues.

### Pull request policy

Each implementation phase from Phase 3 onward, including any later phases added to this specification, MUST be delivered as its own git branch and pull request.

- Do not mix two phases in one pull request.
- Do not commit Phase N+1 work onto a Phase N pull request.
- Finish, review, and merge the current phase before starting the next.
- The Phase 0–2 baseline may be the initial commit and push to the default branch. From Phase 3 onward, every phase is a separate branch and pull request.

---

# 2. Product definition

## 2.1 Product overview

RailOps is an internal railway operations management and analytics platform.

The application enables railway personnel to:

- Manage railway stations.
- Maintain basic railway infrastructure information.
- Register and track operational incidents.
- Import train schedule information from external systems.
- Monitor train delays.
- Analyse operational performance.
- Generate downloadable PDF reports.
- Visualise railway stations and incidents geographically.

The application should resemble a simplified internal railway operations tool, not a public railway booking website.

## 2.2 Target users

Three user roles are required.

### Administrator

Can:
- Manage users and roles.
- Create and manage stations.
- Manage railway lines.
- View and manage all incidents.
- Access analytics.
- Generate and download reports.
- View integration status.
- Manage application configuration where appropriate.

### Dispatcher

Can:
- View stations.
- Register incidents.
- Update incidents.
- Change incident status.
- View operational analytics.
- View railway infrastructure.

Cannot:
- Manage users.
- Change application-wide security settings.

### Viewer

Can:
- View stations.
- View incidents.
- View dashboards and analytics.
- View geographical information.

Cannot:
- Create or modify operational records.
- Generate administrative reports unless explicitly granted permission.

Implement permissions using Django Groups and permissions, not hardcoded checks scattered throughout views.

## 2.3 Functional scope

### In scope

1. Authentication and authorization.
2. Railway infrastructure management.
3. Incident management.
4. Train timetable import.
5. Delay tracking.
6. Analytics dashboard.
7. REST API.
8. External service integration.
9. PDF reporting.
10. Geospatial functionality.
11. Automated testing.
12. CI/CD.
13. Docker-based deployment.
14. Security scanning and documentation.

### Out of scope

Do not implement:

- Railway ticket booking.
- Payment processing.
- Real-time GPS tracking.
- Train control systems.
- Signalling systems.
- Passenger accounts.
- Mobile applications.
- Microservices.
- Machine learning or predictive analytics.
- Complex railway route optimisation.
- Public API access.
- Enterprise SSO.

The application is an operational demonstration platform, not a safety-critical railway control system.

---

# 3. Technology stack

Use the following stack.

| Component | Technology | Purpose |
|---|---|---|
| Language | Python 3.13 | Backend |
| Framework | Django | Main application |
| API | Django REST Framework | REST endpoints |
| Database | PostgreSQL | Persistent storage |
| Geospatial database | PostGIS | Spatial queries |
| Geospatial ORM | GeoDjango | Geographic models |
| Frontend | Django Templates | Server-side rendering |
| UI | Bootstrap 5 | Responsive styling |
| JavaScript | Vanilla JavaScript | Interactive functionality |
| Charts | Chart.js | Analytics visualisation |
| Data processing | Pandas | Reporting and data analysis |
| PDF | WeasyPrint | PDF generation |
| HTTP client | HTTPX | External integrations |
| Testing | Pytest, pytest-django | Automated testing |
| API documentation | drf-spectacular | OpenAPI |
| Linting | Ruff | Code quality |
| Type checking | mypy | Static analysis |
| Security | Bandit, pip-audit | Security checks |
| Containerization | Docker | Deployment |
| CI/CD | GitHub Actions | Automation |
| Web server | Gunicorn | WSGI application server |
| Reverse proxy | Nginx | HTTP routing and static files |

### Version policy

The agent must verify compatible, supported stable versions of all dependencies before installing them.

Do not blindly install the latest versions.

Use:
- `pyproject.toml` for dependency declarations.
- `uv.lock` for reproducible dependency resolution.
- Compatible versions of Django, DRF and GeoDjango.
- A Python version supported by the chosen Django release.

If the specified Python version is incompatible with the selected framework release, report the conflict and recommend a supported version rather than introducing an unsupported configuration.

Pin Docker image versions. Avoid floating `latest` tags.

---

# 4. Architecture

## 4.1 Architectural style

Implement a modular monolith.

All application modules run inside one Django project and share one PostgreSQL database.

Do not introduce microservices.

Organise the code around business capabilities rather than technical layers alone.

The main modules are:

- Accounts.
- Infrastructure.
- Incidents.
- Timetables.
- Integrations.
- Analytics.
- Reports.

## 4.2 Project structure

Use the following target structure:

```text
railops/
│
├── manage.py
├── pyproject.toml
├── uv.lock
├── README.md
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yaml
│
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       ├── test.py
│       └── production.py
│
├── apps/
│   ├── accounts/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── permissions.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── api/
│   │   ├── templates/
│   │   └── tests/
│   │
│   ├── infrastructure/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── selectors.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── api/
│   │   ├── templates/
│   │   └── tests/
│   │
│   ├── incidents/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── selectors.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── api/
│   │   ├── templates/
│   │   └── tests/
│   │
│   ├── timetables/
│   ├── integrations/
│   ├── analytics/
│   └── reports/
│
├── templates/
│   ├── base.html
│   ├── components/
│   ├── registration/
│   ├── dashboard/
│   └── errors/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── tests/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
│
├── scripts/
│
├── docs/
│
└── .github/
    └── workflows/
        ├── ci.yml
        └── deploy.yml
```

This is the target organisation, not a requirement to create empty files for every possible feature immediately.

Each Django app should own its models, business logic, API, templates and tests where appropriate.

## 4.3 Separation of responsibilities

Use the following conventions.

**Models**

Responsible for:
- Persistent data structure.
- Database constraints.
- Relationships.
- Simple model-level behaviour.
- Domain invariants that naturally belong to the entity.

Do not put the entire business logic inside model methods.

**Services**

Responsible for:
- Business operations.
- Multi-model modifications.
- State transitions.
- External integration orchestration.
- Transaction boundaries.

**Selectors**

Responsible for:
- Complex read queries.
- Reusable query construction.
- Optimised data retrieval.

Do not create selectors for trivial queries that are only used once.

**Views**

Responsible for:
- HTTP request handling.
- Input validation through forms or serializers.
- Calling services/selectors.
- Returning HTTP responses.

Views must not contain substantial business logic.

**Serializers**

Responsible for:
- API input validation.
- Output representation.
- Nested representation where justified.

**Forms**

Responsible for:
- Server-rendered HTML form validation.
- User-friendly validation errors.

**Integrations**

Responsible for:
- External HTTP communication.
- Authentication with external services.
- External payload validation.
- Mapping external data to internal representations.

## 4.4 Dependency direction

Follow this dependency convention:

```text
HTTP / API / Templates
          |
          v
       Services
          |
          v
       Models / ORM
          |
          v
       PostgreSQL
```

External integrations must be isolated behind dedicated clients and services.

Business logic must not depend directly on HTTP request objects.

Avoid circular imports between Django apps.

Use dependency injection where it genuinely improves testing or allows alternative implementations, especially for external integrations.

---

# 5. Database design

Use PostgreSQL with PostGIS.

The database must use proper relational modelling, constraints, indexes and migrations.

## 5.1 User

Use Django's built-in authentication framework.

Create a custom user model before the first migration.

Prefer `AbstractUser` unless a concrete requirement justifies a more complex user model.

Additional fields:

- `created_at`
- `updated_at`
- `is_active`

Use Django Groups for roles.

Do not implement custom password storage.

## 5.2 Station

Fields:

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| name | CharField | Station name |
| code | CharField | Unique station code |
| city | CharField | City |
| location | PointField | Geographic coordinates |
| is_active | BooleanField | Operational status |
| created_at | DateTimeField | Creation time |
| updated_at | DateTimeField | Last modification |

Requirements:
- Unique station code.
- Geographic location using SRID 4326.
- Database index for spatial queries.
- Validation of required fields.
- Protection against deletion when referenced by operational records.

Use GeoDjango `PointField` with `geography=True` where appropriate.

## 5.3 RailwayLine

Fields:

- UUID primary key.
- Name.
- Unique code.
- Start station.
- End station.
- Optional geographic geometry.
- Active status.
- Created and updated timestamps.

A railway line should reference stations through explicit relationships.

Do not assume that a line's geographical geometry can always be reconstructed from station coordinates.

## 5.4 Incident

Fields:

- UUID primary key.
- Title.
- Description.
- Station.
- Optional railway line.
- Category.
- Severity.
- Status.
- Reporter.
- Assigned user.
- Reported timestamp.
- Updated timestamp.
- Resolved timestamp.

Incident categories:

- Infrastructure.
- Technical failure.
- Signal failure.
- Track obstruction.
- Weather.
- Operational delay.
- Other.

Severity:

- Low.
- Medium.
- High.
- Critical.

Status:

- Open.
- In progress.
- Resolved.
- Closed.

Implement valid status transitions.

For example:

```text
OPEN
 |
 v
IN_PROGRESS
 |
 v
RESOLVED
 |
 v
CLOSED
```

Do not allow arbitrary transitions without validation.

Resolution timestamps must be set consistently when an incident is resolved and handled correctly if the incident is reopened.

Use database transactions for operations that modify multiple related records.

## 5.5 IncidentEvent

Create an immutable incident history.

Fields:

- UUID.
- Incident.
- Actor.
- Event type.
- Previous status.
- New status.
- Description.
- Timestamp.

Examples:
- Incident created.
- Status changed.
- Severity changed.
- Incident assigned.
- Incident resolved.

History must be created through the appropriate business service.

Regular users must not be able to edit or delete historical events.

## 5.6 TrainService

Fields:

- UUID.
- External identifier.
- Train number.
- Origin station.
- Destination station.
- Service date.
- Source.
- Imported timestamp.

The external identifier and service date should be uniquely constrained together where appropriate.

## 5.7 ScheduledStop

Represents a train's stop at a station.

Fields:

- Train service.
- Station.
- Stop sequence.
- Scheduled arrival.
- Scheduled departure.
- Actual arrival.
- Actual departure.

Add a uniqueness constraint for service plus stop sequence.

Use timezone-aware datetimes.

## 5.8 Delay

Fields:

- UUID.
- Train service.
- Scheduled stop.
- Delay duration in seconds.
- Recorded timestamp.
- Source.

Do not store redundant delay information without defining how it is derived and updated.

Document the distinction between the scheduled time, actual time and calculated delay.

## 5.9 ExternalSyncRun

Track each integration execution.

Fields:

- UUID.
- Integration name.
- Started timestamp.
- Finished timestamp.
- Status.
- Records processed.
- Records created.
- Records updated.
- Error summary.

Never store credentials or complete sensitive external payloads in logs.

## 5.10 Report

Fields:

- UUID.
- Report type.
- Reporting period start.
- Reporting period end.
- Requested by.
- Status.
- Generated timestamp.
- File storage reference.
- Error summary.

Store generated files outside the source repository.

Use a configurable storage backend. Do not store large PDF binaries directly in PostgreSQL.

## 5.11 Database conventions

All models must follow these conventions:

- Use explicit `related_name` values.
- Define meaningful `__str__` methods.
- Use UUID primary keys for externally referenced entities where justified.
- Define appropriate `on_delete` behaviour.
- Add indexes based on query patterns.
- Use `UniqueConstraint` and `CheckConstraint` where appropriate.
- Use migrations for every schema modification.
- Never modify existing migrations to accommodate already-applied production changes.
- Avoid unnecessary database fields that can be derived efficiently.

Use `select_related()` and `prefetch_related()` to prevent N+1 queries.

Do not add indexes indiscriminately. Document important indexes and their purpose.

---

# 6. Backend implementation

## 6.1 Django configuration

Configure:

- Separate development, test and production settings.
- Environment-based configuration.
- Custom user model.
- PostgreSQL/PostGIS connection.
- Static and media file handling.
- Logging.
- Authentication.
- Middleware.
- Allowed hosts.
- CSRF trusted origins.
- Security settings.

Use `django-environ` or `pydantic-settings` if it provides meaningful value. Do not introduce multiple competing configuration systems.

Secrets must never be committed to Git.

Provide `.env.example` with placeholders.

## 6.2 Authentication

Implement:

- Login.
- Logout.
- Password change.
- Password reset.
- Session management.
- Role-based access.

Use Django's standard authentication mechanisms.

Use secure password reset workflows.

For the MVP, email delivery can use a development console backend and a configurable production SMTP backend.

Do not build custom JWT authentication for the server-rendered frontend.

The REST API should use an explicitly documented authentication mechanism. Session authentication is sufficient for the browser-based MVP.

## 6.3 Infrastructure module

Implement CRUD operations for:

- Stations.
- Railway lines.

Features:
- List.
- Detail.
- Create.
- Update.
- Deactivate.
- Search.
- Filtering.
- Pagination.

Prefer deactivation over deletion for infrastructure referenced by operational records.

Use Django ModelForms for server-rendered operations.

## 6.4 Incident module

Implement the complete incident lifecycle.

Required functionality:

1. Register incident.
2. View incident details.
3. Update incident.
4. Assign incident.
5. Change severity.
6. Change status.
7. Display incident history.
8. Filter incidents.
9. Search incidents.
10. Display associated station.

Implement state transitions in a service function or service class.

Example interface:

```python
def transition_incident(
    *,
    incident_id: UUID,
    new_status: Incident.Status,
    actor: User,
    comment: str | None = None,
) -> Incident: ...
```

The implementation must:
- Verify that the incident exists.
- Verify the actor has permission.
- Validate the transition.
- Update the incident.
- Create an immutable history event.
- Execute related writes atomically.
- Return the updated incident.

Consider `select_for_update()` to prevent conflicting simultaneous state changes.

Do not use it unnecessarily for ordinary read operations.

## 6.5 Timetable module

Implement:
- Train service listing.
- Train service detail.
- Scheduled stops.
- Actual arrival and departure information.
- Delay calculation.
- Filtering by date and station.

Delay calculations must handle:
- Missing actual timestamps.
- Early arrivals.
- Overnight services.
- Timezone differences.
- Duplicate imported data.

Represent delays consistently in seconds internally.

Display user-friendly units in the frontend.

## 6.6 Pagination and filtering

All potentially large lists must support pagination.

Use:
- Django pagination for HTML.
- DRF pagination for API endpoints.
- Search fields where useful.
- Validated filters.

Never load the entire incident database into application memory to render a list.

---

# 7. REST API

Use Django REST Framework.

Expose API version 1.

Base path:

`/api/v1/`

## 7.1 Required endpoints

### Stations

| Method | Endpoint | Description |
|---|---|---|
| GET | `/stations/` | List stations |
| GET | `/stations/{id}/` | Station details |
| POST | `/stations/` | Create station |
| PATCH | `/stations/{id}/` | Update station |

### Incidents

| Method | Endpoint | Description |
|---|---|---|
| GET | `/incidents/` | List incidents |
| GET | `/incidents/{id}/` | Incident details |
| POST | `/incidents/` | Register incident |
| PATCH | `/incidents/{id}/` | Update incident |
| POST | `/incidents/{id}/transition/` | Change status |

### Timetables

| Method | Endpoint | Description |
|---|---|---|
| GET | `/services/` | List train services |
| GET | `/services/{id}/` | Service details |
| GET | `/services/{id}/stops/` | Scheduled stops |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/overview/` | General statistics |
| GET | `/analytics/incidents/` | Incident statistics |
| GET | `/analytics/delays/` | Delay statistics |

### Reports

| Method | Endpoint | Description |
|---|---|---|
| GET | `/reports/` | List reports |
| POST | `/reports/` | Request report |
| GET | `/reports/{id}/` | Report details |
| GET | `/reports/{id}/download/` | Download PDF |

## 7.2 API conventions

- Use appropriate HTTP methods.
- Return correct status codes.
- Validate all incoming data.
- Use consistent error response structures.
- Implement pagination.
- Implement filtering.
- Document permissions.
- Avoid exposing internal database details.
- Do not expose stack traces.
- Document request and response schemas.

Use serializers rather than manually constructing JSON in views.

Use `drf-spectacular` to generate OpenAPI documentation.

Provide a browsable API during development.

## 7.3 API security

Apply permissions per endpoint and action.

Examples:
- Viewer: GET access.
- Dispatcher: GET and incident creation/update.
- Administrator: full administrative API access.

Test authorization explicitly. Hiding a button in the frontend is not access control.

---

# 8. External integration

## 8.1 Integration objective

Import railway timetable information from an external provider.

The integration must demonstrate production-style communication with unreliable external services.

Do not invent a railway provider or claim that an unofficial API is a supported production service.

First investigate available providers and their:
- API documentation.
- Authentication.
- Rate limits.
- Data format.
- Terms of use.
- Availability.
- Geographic coverage.

If a suitable API cannot be used, implement a local simulated provider behind the same integration interface.

A CSV import should also be available as a deterministic fallback.

## 8.2 Integration architecture

Use the adapter pattern.

```text
IntegrationService
       |
       v
RailwayProviderInterface
       |
       +---- ExternalRailwayAPIClient
       |
       +---- MockRailwayProvider
       |
       +---- CSVRailwayProvider
```

Define clear interfaces for:
- Fetching train services.
- Fetching scheduled stops.
- Normalising provider data.

Use Pydantic models or equivalent typed schemas to validate external payloads before persisting data.

Do not allow unvalidated provider responses to flow directly into database models.

## 8.3 HTTP client requirements

Use HTTPX.

Requirements:
- Explicit connection timeout.
- Explicit read timeout.
- Request timeout handling.
- HTTP status validation.
- Limited retry for transient errors.
- Exponential backoff.
- Respect `Retry-After` where appropriate.
- Structured logging.
- Proper resource cleanup.

Do not retry permanent errors such as invalid authentication or malformed requests.

Do not retry non-idempotent operations blindly.

## 8.4 Synchronization

Implement a synchronization service.

The process:

1. Start synchronization.
2. Create `ExternalSyncRun`.
3. Fetch external data.
4. Validate data.
5. Normalise records.
6. Deduplicate.
7. Persist records.
8. Update synchronization statistics.
9. Mark success or failure.
10. Record errors safely.

The synchronization process must be idempotent.

Running it twice with the same data must not create duplicate train services or scheduled stops.

Use database uniqueness constraints and appropriate `update_or_create()` or bulk operations.

Use transactions at appropriate boundaries.

For the MVP, a Django management command is sufficient to trigger synchronization.

Do not introduce Celery, Redis or RabbitMQ unless asynchronous execution becomes necessary. If background processing is later added, keep it as an optional extension.

---

# 9. Pandas and analytics

## 9.1 Purpose

Use Pandas to demonstrate practical data processing and reporting.

Do not use Pandas for ordinary database filtering or simple counts that PostgreSQL can calculate more efficiently.

Prefer:
- Django ORM aggregation for routine dashboard metrics.
- SQL for large database aggregations.
- Pandas for transformations, multi-source datasets and report preparation.

## 9.2 Required analytics

### Incident analytics

Calculate:
- Total incidents.
- Open incidents.
- Resolved incidents.
- Incidents by severity.
- Incidents by category.
- Average resolution time.
- Median resolution time.
- Incident volume by month.
- Incidents per station.

### Delay analytics

Calculate:
- Total train services.
- Delayed services.
- Average delay.
- Median delay.
- Maximum delay.
- Delay by station.
- Delay by day.
- On-time performance percentage.

Define an explicit on-time threshold and document it.

Do not silently treat missing actual arrival data as zero delay.

## 9.3 Analytics architecture

```text
Database
   |
   v
Query / Aggregation Layer
   |
   v
Analytics Service
   |
   v
Pandas DataFrame
   |
   v
Report / Dashboard Data
```

Keep data retrieval separate from statistical transformations.

Use pure functions for calculations wherever possible.

Example interface:

```python
def calculate_incident_metrics(
    records: list[dict[str, object]],
) -> IncidentMetrics: ...
```

Define typed return objects rather than exposing arbitrary DataFrame structures to views.

## 9.4 Performance

- Avoid fetching unnecessary columns.
- Filter at database level.
- Use aggregation before loading data into Pandas.
- Avoid loading unbounded datasets.
- Process reports in bounded date ranges.
- Measure memory consumption for larger datasets.

Include tests for:
- Empty datasets.
- Null values.
- Invalid dates.
- Unresolved incidents.
- Outliers.
- Different reporting periods.

---

# 10. PDF generation

Use WeasyPrint.

## 10.1 Report types

Implement one primary report initially:

**Monthly Railway Operations Report**

Contents:
1. Report title.
2. Reporting period.
3. Generation timestamp.
4. Overall operational summary.
5. Incident statistics.
6. Severity breakdown.
7. Incident trends.
8. Average resolution time.
9. Delay statistics.
10. Most problematic stations.

## 10.2 Implementation flow

```text
User requests report
        |
        v
Validate request and permissions
        |
        v
Retrieve relevant data
        |
        v
Calculate statistics
        |
        v
Build report context
        |
        v
Render HTML template
        |
        v
Generate PDF
        |
        v
Store file
        |
        v
Return downloadable report
```

Use dedicated report templates.

Do not construct PDF content by concatenating HTML strings.

## 10.3 Security and reliability

- Validate report period.
- Limit maximum report range.
- Restrict downloads by permission.
- Prevent path traversal.
- Avoid loading arbitrary external resources during PDF rendering.
- Use controlled static assets.
- Set file size limits where appropriate.
- Clean up temporary files.
- Handle PDF generation errors.

For a small MVP, synchronous PDF generation is acceptable if report size is bounded.

Document how this would change for large reports requiring background jobs.

---

# 11. Geospatial functionality

## 11.1 Implementation

Use GeoDjango and PostGIS.

The main spatial entity is RailwayStation.

Use geographic points with SRID 4326.

Implement:
- Station coordinates.
- Spatial database indexing.
- Nearby station search.
- Distance calculations.
- Geographic filtering.
- Map visualisation.

## 11.2 Map interface

Use Leaflet.js with OpenStreetMap-compatible tile providers.

Display:
- Railway stations.
- Station names.
- Active incidents.
- Incident severity markers.

Provide:
- Marker clustering if necessary.
- Station details on marker selection.
- Basic map filtering.

Check tile-provider terms and usage restrictions. Do not assume public tile servers are suitable for unrestricted production use.

## 11.3 Spatial queries

Demonstrate at least two meaningful operations:

1. Find stations within a radius.
2. Find the nearest station.

Use GeoDjango spatial query functions.

Ensure spatial indexes are created through migrations.

Write tests against a PostGIS-enabled test database.

Do not silently replace spatial queries with approximate calculations in production.

---

# 12. Frontend

## 12.1 General approach

Use server-rendered Django Templates.

Use Bootstrap 5 for layout and responsive components.

Use vanilla JavaScript for interactive elements.

Use Chart.js for charts.

Do not introduce React or a separate frontend build system.

The objective is to demonstrate proficiency with Django's traditional full-stack capabilities.

## 12.2 Main layout

Create a professional internal operations dashboard.

Main navigation:

- Dashboard.
- Stations.
- Railway lines.
- Incidents.
- Train services.
- Analytics.
- Reports.
- Administration.

Display navigation items based on user permissions.

## 12.3 Dashboard

Display:
- Total incidents.
- Open incidents.
- Critical incidents.
- Average resolution time.
- Delayed services.
- Incident trend chart.
- Incident severity chart.
- Recent incidents.
- Recently imported train services.

All metrics must come from actual persisted data.

Do not use hardcoded numbers in the finished application.

## 12.4 User experience

Requirements:
- Responsive layout.
- Consistent navigation.
- Clear forms.
- Field-level validation errors.
- Confirmation for destructive operations.
- Success/error messages.
- Empty states.
- Loading indicators where needed.
- Pagination.
- Accessible labels.
- Keyboard navigation.
- Semantic HTML.

Use Django template inheritance.

Avoid duplicated markup.

Create reusable template components for:
- Navigation.
- Tables.
- Pagination.
- Form fields.
- Status badges.
- Severity badges.
- Alert messages.

## 12.5 JavaScript

JavaScript should progressively enhance the server-rendered application.

Use it for:
- Chart rendering.
- Map interactions.
- Small dynamic form behaviours.
- Confirmation dialogs.
- Optional asynchronous filters.

Do not move business logic into the browser.

Never rely on frontend validation alone.

---

# 13. Testing strategy

Testing is mandatory, not optional.

Use Pytest and pytest-django.

## 13.1 Unit tests

Test:
- Incident state transitions.
- Permission rules.
- Delay calculations.
- Incident statistics.
- Date range validation.
- Data normalisation.
- External payload validation.
- Report context generation.

Prefer testing public behaviour rather than private implementation details.

## 13.2 Model tests

Test:
- Required fields.
- Unique constraints.
- Relationships.
- Check constraints.
- Valid status values.
- Geographic fields.
- Timestamp behaviour.

## 13.3 API tests

Test:
- Correct status codes.
- Successful requests.
- Invalid requests.
- Missing authentication.
- Insufficient permissions.
- Pagination.
- Filtering.
- Serialization.
- Error responses.

## 13.4 Integration tests

Test:
- Database interactions.
- Incident creation and history recording.
- External synchronization.
- Duplicate imports.
- Failed external API calls.
- PDF generation.
- Spatial queries.

Mock external HTTP requests. Automated tests must not depend on a live third-party API.

Use a PostGIS-enabled test database for spatial tests.

## 13.5 Security tests

Verify:
- Unauthorized users cannot access protected pages.
- Viewers cannot modify incidents.
- Dispatchers cannot manage users.
- Users cannot access another user's restricted resources.
- CSRF protection is active.
- Invalid input is rejected.
- File download permissions are enforced.
- Secrets are not exposed in responses or logs.

## 13.6 Test fixtures

Use factories or well-structured fixtures.

Prefer `factory_boy` if multiple models have complex relationships.

Avoid enormous fixtures that obscure the test scenario.

## 13.7 Coverage

Aim for:
- At least 80% coverage of application business logic.
- Strong coverage of permission and state-transition code.
- Explicit coverage of error-handling paths.

Do not optimise for coverage percentage at the expense of meaningful assertions.

---

# 14. Code quality and static analysis

Configure Ruff, mypy and Bandit.

## 14.1 Ruff

Enable:
- Pyflakes.
- pycodestyle.
- pyupgrade.
- Import sorting.
- Bugbear.
- Simplification rules.
- Security-relevant linting rules where appropriate.

Use consistent formatting.

Set a reasonable line length.

## 14.2 Mypy

Use strict type checking for application code where compatible.

Add type annotations to:
- Services.
- Selectors.
- Utility functions.
- Integration clients.
- Analytics functions.

Use Django typing support, such as `django-stubs`, if it is compatible with the chosen stack.

Avoid excessive `Any`.

Do not silence type errors globally.

## 14.3 Bandit

Scan application code for common security issues.

Review findings manually.

Do not suppress findings without justification.

## 14.4 Dependency scanning

Run `pip-audit` against the locked dependencies.

Document how vulnerabilities are evaluated and fixed.

Keep dependencies minimal.

Do not install packages simply because they are popular.

---

# 15. Security requirements

Security must be considered throughout implementation.

## 15.1 Application security

- Use Django's password hashing.
- Use CSRF protection.
- Use secure session settings.
- Configure `ALLOWED_HOSTS`.
- Configure trusted origins.
- Enable secure cookies in production.
- Use HTTPS in production.
- Enable appropriate security headers.
- Protect administrative functionality.
- Apply object-level permission checks where needed.

## 15.2 Input validation

Validate:
- User input.
- API payloads.
- CSV files.
- External API responses.
- Report date ranges.
- Geographic coordinates.
- Uploaded file types and sizes.

Do not trust external data.

## 15.3 Database security

- Use a dedicated database user.
- Do not use PostgreSQL superuser credentials in production.
- Store database credentials in environment variables or a secret manager.
- Do not expose the database publicly.
- Use least-privilege access.
- Configure backups.

## 15.4 File security

- Store generated PDFs outside static source directories.
- Prevent arbitrary file paths.
- Verify access before downloading.
- Do not expose internal storage paths.
- Avoid unsafe file rendering.

## 15.5 Logging

Use structured logging.

Log:
- Application errors.
- Failed authentication attempts where appropriate.
- Integration failures.
- Synchronization results.
- Report generation failures.

Do not log:
- Passwords.
- Tokens.
- API keys.
- Session cookies.
- Sensitive personal information.
- Full confidential external payloads.

---

# 16. Docker and deployment

## 16.1 Local development

Use Docker Compose for infrastructure.

Services:

- PostgreSQL with PostGIS.
- Django application.

The Django application may run locally outside Docker during development if this improves the developer experience.

Provide a convenient development setup.

## 16.2 Production Dockerfile

Create a separate production-oriented Dockerfile.

Requirements:
- Multi-stage build where useful.
- Non-root user.
- Minimal runtime dependencies.
- Pinned base image.
- No secrets in image layers.
- Proper process handling.
- Gunicorn.
- Static asset collection.
- Health check endpoint.

Do not run Django development server in production.

Do not run migrations automatically in every application worker startup.

Provide a dedicated migration step.

## 16.3 Production deployment

Target a small VPS or a compatible hosting platform.

Deployment process:

1. Build Docker image.
2. Run tests and security checks.
3. Push image to container registry.
4. Connect to deployment environment.
5. Run database migrations.
6. Start new application version.
7. Check health endpoint.
8. Run smoke tests.
9. Verify application availability.
10. Retain the previous image for rollback.

Document the deployment process.

Do not claim zero-downtime deployment unless the infrastructure actually supports it.

## 16.4 Environment variables

Provide `.env.example` containing:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.development

SECRET_KEY=replace-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=railops
DB_USER=railops
DB_PASSWORD=replace-me
DB_HOST=localhost
DB_PORT=5432

EXTERNAL_RAILWAY_API_URL=
EXTERNAL_RAILWAY_API_KEY=

MEDIA_ROOT=/app/media
STATIC_ROOT=/app/staticfiles
```

Add other required variables when implementing their features.

Never include real credentials in committed files.

---

# 17. CI/CD

Use GitHub Actions.

## 17.1 Pull request workflow

Run:

1. Dependency installation from lockfile.
2. Ruff formatting check.
3. Ruff lint.
4. Mypy.
5. Bandit.
6. Dependency vulnerability scan.
7. Django system checks.
8. Unit tests.
9. Integration tests.
10. Coverage reporting.

Use PostgreSQL with PostGIS for integration tests.

## 17.2 Main branch workflow

After successful checks:

1. Build production image.
2. Run container smoke checks.
3. Push image to registry.
4. Deploy according to configured environment.
5. Execute migrations as a dedicated step.
6. Execute post-deployment smoke tests.

Require approval for production deployment if the hosting environment supports it.

## 17.3 Pipeline requirements

- Use GitHub Secrets for sensitive configuration.
- Pin third-party GitHub Actions to reviewed versions or commit SHAs.
- Cache dependencies safely.
- Avoid exposing secrets to untrusted pull requests.
- Fail the pipeline on critical quality issues.

---

# 18. Documentation

Documentation is part of the deliverable.

## README.md

Include:
- Project overview.
- Screenshots.
- Technology stack.
- Architecture overview.
- Main features.
- Prerequisites.
- Installation instructions.
- Local development.
- Database setup.
- Migrations.
- Running tests.
- Linting and type checking.
- API documentation.
- Deployment instructions.
- Known limitations.

## Architecture documentation

Explain:
- Why a modular monolith was selected.
- Why Django was selected.
- Application boundaries.
- Database design.
- Integration architecture.
- Analytics processing.
- Report generation.
- Security boundaries.

## API documentation

Include:
- Endpoint descriptions.
- Authentication.
- Permissions.
- Example requests.
- Example responses.
- Error responses.
- Pagination and filtering.

## Security documentation

Explain:
- Authentication.
- Authorization.
- Secret management.
- Input validation.
- External integration security.
- File access restrictions.
- Dependency scanning.
- Production configuration.

## Architecture Decision Records

Write ADRs for meaningful decisions.

At minimum:

- ADR-001: Modular monolith.
- ADR-002: PostgreSQL and PostGIS.
- ADR-003: External integration adapter.
- ADR-004: Server-rendered frontend.
- ADR-005: Analytics and Pandas.
- ADR-006: PDF generation and storage.

Each ADR must explain:
- Context.
- Options considered.
- Decision.
- Consequences.
- Trade-offs.

---

# 19. Development phases and implementation tasks

Implement the project in the following order.

Do not attempt to build everything in one generation.

From Phase 3 onward, deliver each phase as its own git branch and pull request. Do not mix phases in one PR. See section 1.3, Pull request policy.

## Phase 0 — Repository inspection and planning

Tasks:

- Inspect existing repository.
- Check Python and package manager.
- Identify existing configuration.
- Create architecture documentation.
- Create implementation backlog.
- Define initial database model relationships.
- Identify dependency compatibility issues.

Deliverables:
- `docs/architecture.md`
- `docs/database-design.md`
- `docs/implementation-status.md`
- Initial ADRs.

Acceptance criteria:
- Architecture is documented.
- Scope is agreed.
- No implementation decisions are based on unverified assumptions.

## Phase 1 — Project foundation

Tasks:

- Initialise Django project.
- Configure settings separation.
- Configure PostgreSQL/PostGIS.
- Create custom user model.
- Configure static and template directories.
- Configure Ruff.
- Configure mypy.
- Configure pytest.
- Configure environment variables.
- Add initial Docker Compose infrastructure.
- Add a health endpoint.
- Add baseline CI workflow.

Acceptance criteria:

- Application starts successfully.
- Database connection works.
- Migrations run.
- Health endpoint responds.
- Tests execute.
- Linting and type checks pass.
- No secrets are committed.

## Phase 2 — Authentication and permissions

Tasks:

- Implement login and logout.
- Implement password reset workflow.
- Create Django Groups.
- Define administrator, dispatcher and viewer permissions.
- Add user management for administrators.
- Implement access restrictions.
- Add tests for role-based access.

Acceptance criteria:

- All three roles work.
- Unauthorized operations are rejected server-side.
- Authentication tests pass.
- Passwords are never stored in plaintext.

## Phase 3 — Railway infrastructure

Tasks:

- Implement Station.
- Implement RailwayLine.
- Create migrations.
- Implement forms.
- Implement CRUD views.
- Implement list filtering.
- Implement pagination.
- Implement station details.
- Add spatial index.
- Write model and view tests.

Acceptance criteria:

- Stations can be created, updated and deactivated.
- Railway lines can be managed.
- Unique station codes are enforced.
- Geographic coordinates are persisted.
- Users see only functionality permitted by their role.

## Phase 4 — Incident management

Tasks:

- Implement Incident.
- Implement IncidentEvent.
- Implement incident services.
- Implement valid status transitions.
- Implement incident assignment.
- Implement filtering and search.
- Implement incident detail and history pages.
- Add transaction handling.
- Add concurrency protection where appropriate.
- Write comprehensive tests.

Acceptance criteria:

- Full incident lifecycle works.
- Every relevant state change is recorded.
- Invalid transitions are rejected.
- Unauthorized modifications are rejected.
- Database consistency is maintained.

## Phase 5 — Timetable and external integration

Tasks:

- Implement TrainService.
- Implement ScheduledStop.
- Implement Delay.
- Define provider interface.
- Implement mock provider.
- Implement CSV import.
- Investigate a real provider.
- Implement HTTPX client if a suitable provider is available.
- Implement payload validation.
- Implement idempotent synchronization.
- Implement ExternalSyncRun.
- Create management command.
- Add integration tests.

Acceptance criteria:

- Timetable records can be imported.
- Duplicate imports do not create duplicates.
- Invalid records are rejected or safely reported.
- External failures do not corrupt existing data.
- Synchronization results are visible.
- The mock provider supports deterministic local development.

## Phase 6 — REST API

Tasks:

- Configure DRF.
- Implement serializers.
- Implement API views/viewsets.
- Implement permissions.
- Implement pagination.
- Implement filtering.
- Implement error handling.
- Configure API versioning.
- Generate OpenAPI documentation.
- Add API tests.

Acceptance criteria:

- Required endpoints work.
- API permissions match user roles.
- Invalid requests return meaningful errors.
- API documentation is available.
- No database internals or stack traces are exposed.

## Phase 7 — Analytics

Tasks:

- Implement database aggregation queries.
- Implement analytics services.
- Implement Pandas transformations.
- Define typed analytics output schemas.
- Implement incident metrics.
- Implement delay metrics.
- Implement date-range filters.
- Add unit tests for edge cases.

Acceptance criteria:

- Analytics use real database data.
- Empty datasets are handled.
- Null values are handled correctly.
- Delay metrics are mathematically consistent.
- Expensive operations are bounded.

## Phase 8 — Dashboard and frontend

Tasks:

- Create base layout.
- Implement responsive navigation.
- Create dashboard.
- Create incident list and details.
- Create station list and details.
- Implement Chart.js visualisations.
- Implement Leaflet map.
- Implement filtering and pagination.
- Add accessible form controls.
- Add empty and error states.

Acceptance criteria:

- Main workflows work through the browser.
- Dashboard metrics are dynamic.
- The map displays persisted station data.
- The interface is usable on desktop and mobile.
- No important operation depends solely on JavaScript.

## Phase 9 — PDF reporting

Tasks:

- Implement Report model.
- Implement report service.
- Create report templates.
- Integrate Pandas analytics.
- Generate PDF using WeasyPrint.
- Implement secure download.
- Add report tests.

Acceptance criteria:

- Monthly report can be generated.
- Data corresponds to the requested period.
- PDF is readable and properly formatted.
- Unauthorized downloads are rejected.
- Failed generation is recorded.

## Phase 10 — Geospatial functionality

Tasks:

- Implement nearby station search.
- Implement nearest station query.
- Implement incident map markers.
- Add spatial filtering.
- Add spatial tests.

Acceptance criteria:

- Spatial queries execute against PostGIS.
- Coordinates are validated.
- Spatial indexes are present.
- Map data comes from the database.

## Phase 11 — Production readiness

Tasks:

- Create production Dockerfile.
- Configure Gunicorn.
- Configure Nginx or the chosen reverse proxy.
- Configure static and media storage.
- Configure logging.
- Configure health checks.
- Configure production security settings.
- Configure database backups.
- Configure CI/CD deployment.
- Test migrations and rollback procedures.
- Perform security review.

Acceptance criteria:

- Application builds successfully.
- Application runs as non-root.
- Production settings are secure.
- Deployment is reproducible.
- Smoke tests pass.
- Rollback procedure is documented.

## Phase 12 — Final verification and interview preparation

Tasks:

- Run full test suite.
- Run all static analysis.
- Run dependency scanning.
- Review application permissions.
- Review database queries.
- Review error handling.
- Review documentation.
- Capture screenshots.
- Prepare architecture diagram.
- Prepare interview talking points.
- Record known limitations.

Acceptance criteria:

- No unresolved critical security issues.
- No failing automated tests.
- All primary features work.
- README supports a clean installation.
- Architecture decisions can be explained.
- The deployed application is demonstrable.

---

# 20. Definition of Done

A feature is not complete merely because its implementation exists.

Every feature must satisfy the following:

### Code
- Follows project architecture.
- Has meaningful names.
- Includes appropriate type annotations.
- Does not duplicate existing functionality.
- Has no unnecessary abstractions.
- Handles expected errors.

### Security
- Validates untrusted input.
- Enforces permissions.
- Does not leak secrets.
- Does not introduce obvious injection or file-access vulnerabilities.

### Tests
- Includes relevant unit tests.
- Includes integration tests where necessary.
- Covers important error cases.
- Passes existing tests.

### Quality
- Ruff passes.
- Mypy passes for configured application scope.
- Bandit findings are reviewed.
- No unexplained suppressions.

### Documentation
- Public interfaces are documented.
- Non-obvious decisions are explained.
- Limitations are recorded.

### Delivery
- The feature works through its intended interface.
- No placeholder implementation is presented as complete.
- The implementation status is updated.

---

# 21. Final MVP acceptance criteria

The project is ready for demonstration when a reviewer can perform this complete workflow:

1. Log in as an administrator.
2. Create a railway station.
3. Create a railway line.
4. Create a dispatcher account.
5. Log in as a dispatcher.
6. Register an incident at the station.
7. Assign the incident.
8. Change its severity.
9. Change its status.
10. Inspect its history.
11. Import train timetable data.
12. View train delays.
13. Open the analytics dashboard.
14. Filter statistics by date.
15. View stations on the geographical map.
16. Generate a monthly PDF report.
17. Download the report.
18. Access the same operational data through REST API endpoints.
19. Verify that a viewer cannot modify operational records.
20. Verify that automated tests and CI checks pass.

The application must use real persisted data for this workflow.

---

# 22. Important engineering constraints

The agent must not:

1. Implement the entire application in one enormous code-generation step.
2. Put business logic inside Django views.
3. Create generic repository abstractions for every model without justification.
4. Use raw SQL where ordinary Django ORM operations are sufficient.
5. Use Pandas to perform simple database aggregations unnecessarily.
6. Introduce microservices.
7. Introduce React.
8. Introduce Kafka, RabbitMQ or Redis without a demonstrated requirement.
9. Use fake external integrations while claiming they are real.
10. Store credentials in source code.
11. Disable security features to make tests pass.
12. Ignore failing tests.
13. Suppress type errors indiscriminately.
14. Generate migrations without checking their correctness.
15. Use SQLite as a substitute for PostgreSQL/PostGIS in integration testing.
16. Build functionality without appropriate authorization checks.
17. Add unnecessary dependencies.
18. Implement advanced features before the MVP works.
19. Leave important TODOs in features marked complete.
20. Claim deployment success without actually verifying the deployment.

---

# 23. Final deliverables

The finished repository must contain:

| Deliverable | Required |
|---|---|
| Working Django application | Yes |
| PostgreSQL/PostGIS database | Yes |
| Server-rendered frontend | Yes |
| REST API | Yes |
| External integration adapter | Yes |
| Mock integration provider | Yes |
| CSV timetable import | Yes |
| Pandas analytics | Yes |
| PDF report generation | Yes |
| Geospatial functionality | Yes |
| Authentication and permissions | Yes |
| Automated tests | Yes |
| Ruff and mypy configuration | Yes |
| Security scanning | Yes |
| Docker configuration | Yes |
| GitHub Actions CI/CD | Yes |
| Deployment documentation | Yes |
| API documentation | Yes |
| Architecture documentation | Yes |
| Screenshots and demo data | Yes |

---

# 24. Expected final report from the agent

When development is complete, provide a final engineering report containing:

1. Project overview.
2. Implemented features.
3. Architecture explanation.
4. Database design.
5. Technology choices and rationale.
6. Test results and coverage.
7. Static analysis results.
8. Security scan results.
9. CI/CD implementation.
10. Deployment instructions.
11. Application screenshots.
12. Known limitations.
13. Potential future improvements.
14. Suggested technical interview questions based on the implementation.

The agent must distinguish clearly between:
- Implemented and tested.
- Implemented but not fully tested.
- Partially implemented.
- Not implemented.
- Blocked by external dependencies.

Do not report unverified functionality as completed.

---

# 25. Guiding principle

Build RailOps as if another developer will inherit and maintain it.

The goal is not to demonstrate how many technologies can be squeezed into one application.

The goal is to demonstrate that you understand how to use these technologies together to solve a coherent business problem.

A small, reliable, well-tested Django application with proper architecture, integrations, analytics, geospatial functionality and deployment is more valuable than a large application full of superficial implementations.

**Definition of success:** A technical interviewer should be able to inspect the repository, run the application, explore the code, execute the tests, and understand why the engineering decisions were made.

End of specification.