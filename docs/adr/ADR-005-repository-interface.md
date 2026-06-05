# ADR-005: Repository Interfaces & Decoupling Design

## Status
Approved

## Context
We want the core business logic of BilgeAPI to be decoupled from the database engine. In Phase 1 we use an in-memory storage, and in Phase 3 we will switch to PostgreSQL. We need to prevent rewriting or modifying endpoints and service classes when the database technology changes.

## Decision
1. **Repository Abstraction**: We will define abstract repositories/interfaces (using Python's `abc.ABC` or Protocols) for every database entity:
   - `IncidentRepository`
   - `DiagnosticRepository`
   - `FindingRepository`
   - `RecommendationRepository`
   - `RepairRequestRepository`
   - `AuditRepository`
   - `WebhookDeliveryRepository`
2. **Dependency Injection**: Routers and service layer classes will request the repositories using FastAPI's dependency injection pattern (e.g. `Depends(get_incident_repository)`).
3. **Phase-Specific Injection**:
   - In Phase 1, `get_xxxx_repository` dependencies will return instances of `InMemoryXXXXRepository` (which are thread-safe singletons).
   - In Phase 3, we will modify the dependency providers to return `PostgresXXXXRepository` (which uses SQLAlchemy async sessions) without altering any endpoints or service logic.

## Consequences
- Clean codebase architecture adhering to Domain-Driven Design (DDD) principles.
- Code changes in database engines do not leak into the controller or business layer.
- Tests can swap repository implementations dynamically via FastAPI's `dependency_overrides`.
