# Implementation Plan — BilgeAPI (Faz 0 & Faz 1 Core)

This plan outlines the architecture, design decisions, and concrete steps to build the first phase (Faz 0 and Faz 1) of `BilgeAPI` — an independent **Incident Intake, Diagnostic, and Repair-Orchestration API** designed for standalone use.

---

## Finalized Decisions

> [!NOTE]
> - **Standalone Service Port**: BilgeAPI runs on port `8100` (standalone) to prevent conflicts with the existing workspace apps.
> - **Isolated DB and Service Prefix**: Service name is `bilgeapi-api`, database name/schema is `bilgeapi`, and environment variables use the `BILGEAPI_` prefix.
> - **Fake Repository Singleton**: For Faz 1, we will implement in-memory/fake repositories that use a thread-safe singleton lock pattern.
> - **Environment-driven Auth Gate**: The auth middleware checks `BILGEAPI_AUTH_MODE` (`disabled` | `api_key` | `jwt`).
>   - In Faz 1, `api_key` mode validates requests against `BILGEAPI_STATIC_KEYS` loaded from env (e.g., `key_1,key_2`).
>   - Missing or invalid keys on write endpoints will return HTTP 401/403. Read/write logic is fully auth-guarded.
>   - Logs will redact key contents.
> - **Dual Audit Logging (JSONL)**: Audit events are written to the in-memory repository and appended to `apps/bilgeapi/audit.log` as structured JSONL. Writing failures will be caught gracefully and will not interrupt the main request flow. Log redaction will filter out any sensitive variables/tokens.
> - **OpenAPI Specifications**: FastAPI's built-in docs endpoints remain enabled, and a utility script `scripts/export_bilgeapi_openapi.py` will generate the static contract file `docs/openapi/bilgeapi_openapi.json`.

---

## Proposed Changes

### Architecture Documents & Implementation Plan
Architecture decision records (ADRs) to freeze core design contract and schemas.

#### [NEW] [ADR-001-postgresql-runtime.md](file:///e:/ai_company_faz12.1/docs/adr/ADR-001-postgresql-runtime.md)
Document decisions on production DB (PostgreSQL) vs development/test DB (SQLite/Fake Repository) and connection patterns.

#### [NEW] [ADR-002-general-incident-intake.md](file:///e:/ai_company_faz12.1/docs/adr/ADR-002-general-incident-intake.md)
Document the standard revised incident payload contract, field constraints, severity levels, and project-aware keys.

#### [NEW] [ADR-003-mock-webhook-adapters.md](file:///e:/ai_company_faz12.1/docs/adr/ADR-003-mock-webhook-adapters.md)
Document the diagnostic & dispatch adapter signatures, parameters, and the security rules for signed webhooks.

#### [NEW] [ADR-004-async-diagnostic-lifecycle.md](file:///e:/ai_company_faz12.1/docs/adr/ADR-004-async-diagnostic-lifecycle.md)
Document the queue-based async workflow status values (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`) and contract.

#### [NEW] [ADR-005-repository-interface.md](file:///e:/ai_company_faz12.1/docs/adr/ADR-005-repository-interface.md)
Document repository interface isolation logic to keep the service layer db-agnostic.

#### [NEW] [bilgeapi_implementation_plan.md](file:///e:/ai_company_faz12.1/docs/bilgeapi_implementation_plan.md)
Project-level implementation plan copying this blueprint into the docs directory.

---

### BilgeAPI Application Skeleton
The core entry point, routing, middleware, and application settings.

#### [NEW] [__init__.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/__init__.py)
Package initialization file.

#### [NEW] [config.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/config.py)
Configuration settings loader utilizing `pydantic-settings` or `os.getenv` with typed options (e.g. `BILGEAPI_AUTH_MODE`, `BILGEAPI_PORT`, etc.).

#### [NEW] [main.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/main.py)
The core FastAPI application bootstrapping routes, custom middleware for auth/auditing, error handlers, and lifecycle hooks.

---

### Data Models & Schemas
Pydantic contracts validating request/response models.

#### [NEW] [incident.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/schemas/incident.py)
Incident input payload and response models, enforcing presence of `project_key`, `correlation_id`, severity enums, and timestamps.

#### [NEW] [diagnostic.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/schemas/diagnostic.py)
Schemas for initiating a diagnostic, checking progress status asynchronously, and displaying diagnostic outcomes (summary, hypothesis, findings, recommendations).

#### [NEW] [repair.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/schemas/repair.py)
Schemas for repair request generation and lifecycle tracking.

#### [NEW] [audit.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/schemas/audit.py)
Pydantic model for audit trail events, capturing actors, entity state changes, and client context.

---

### Repository Interfaces & Fake Implementations
Data layer abstraction ensuring clean isolation from database implementation.

#### [NEW] [interface.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/repositories/interface.py)
Abstract base interfaces/protocols defining method signatures for `IncidentRepository`, `DiagnosticRepository`, `FindingRepository`, `RecommendationRepository`, `RepairRequestRepository`, `AuditRepository`, and `WebhookDeliveryRepository`.

#### [NEW] [memory.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/repositories/memory.py)
In-memory implementation of all repository interfaces using thread-safe data structures.

---

### API Routers
Routes registering endpoints.

#### [NEW] [health.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/routers/health.py)
`/health` endpoint returning system metrics, auth configuration status, and health indicators.

#### [NEW] [catalog.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/routers/catalog.py)
`/v1/catalog` endpoint returning available diagnostics/repair dispatch adapters details.

#### [NEW] [incidents.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/routers/incidents.py)
`/v1/incidents` endpoint mappings for creating, retrieving, and listing incident records.

#### [NEW] [audit.py](file:///e:/ai_company_faz12.1/apps/bilgeapi/routers/audit.py)
`/v1/audit-events` read endpoint for the auditor component.

---

### Utility Scripts
Utility script to export openapi.json.

#### [NEW] [export_bilgeapi_openapi.py](file:///e:/ai_company_faz12.1/scripts/export_bilgeapi_openapi.py)
Script to automatically start the FastAPI app in a dry-run context and save its OpenAPI schema to `docs/openapi/bilgeapi_openapi.json`.

---

### Testing Suite
TDD verification structure.

#### [NEW] [conftest.py](file:///e:/ai_company_faz12.1/tests/unit/bilgeapi/conftest.py)
FastAPI test client setup using the memory repository implementations.

#### [NEW] [test_health_catalog.py](file:///e:/ai_company_faz12.1/tests/unit/bilgeapi/test_health_catalog.py)
Unit tests for the health endpoint and catalog description payload.

#### [NEW] [test_incident_flow.py](file:///e:/ai_company_faz12.1/tests/unit/bilgeapi/test_incident_flow.py)
Unit and contract tests verifying incident validation, audit recording, database listing, and key mapping rules.

---

## Verification Plan

### Automated Tests
Run the standard test runner to assert all components are working cleanly. We target a coverage of >80% for new components:
```bash
pytest tests/unit/bilgeapi --cov=apps/bilgeapi --cov-report=term-missing
```

### Manual Verification
1. Start the API locally in standalone development mode:
   ```bash
   uvicorn apps.bilgeapi.main:app --port 8100 --reload
   ```
2. Verify endpoints using curl command requests:
   - Check health status: `curl http://127.0.0.1:8100/health`
   - Retrieve catalog: `curl http://127.0.0.1:8100/v1/catalog`
   - Post an incident and verify audit trace entries.
