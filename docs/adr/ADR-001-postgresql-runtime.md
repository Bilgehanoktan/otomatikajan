# ADR-001: PostgreSQL Runtime Database Design

## Status
Approved

## Context
BilgeAPI is a standalone service that will handle incident intake, diagnostic execution, and repair orchestration. It needs a reliable, ACID-compliant database. However, developer environments and unit tests should run fast and without requiring a local PostgreSQL instance.

## Decision
1. **Production Database**: PostgreSQL is the primary database for storing incidents, diagnostics, findings, recommendations, and repair requests.
2. **Schema & Database Naming**:
   - Database name: `bilgeapi`
   - Database schema: `bilgeapi`
3. **Environment Prefix**: All database and system settings will be prefixed with `BILGEAPI_` (e.g., `BILGEAPI_DATABASE_URL`).
4. **Development/Test Database**: For Phase 1, the database layer will be abstract. Local development and testing will use a thread-safe in-memory/fake repository implementation. This guarantees zero-dependency local runs and extremely fast tests. Phase 3 will introduce the SQL Alchemy + PostgreSQL repository implementations.

## Consequences
- Clean separation between the service layer and the actual data store.
- Local development runs standalone without needing PostgreSQL setup.
- Testing is database-independent, preventing flaky test runs.
