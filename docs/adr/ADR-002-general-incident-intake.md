# ADR-002: General Incident Intake Contract

## Status
Approved

## Context
BilgeAPI needs to intake incidents from multiple external projects, environments, and source systems. To facilitate diagnosis, tracking, and tracing, the payload contract must contain mandatory correlation and structural metadata fields.

## Decision
The incident intake model will enforce the following JSON payload contract:

```json
{
  "project_key": "payment-platform",
  "source_system": "backend-api",
  "environment": "production",
  "kind": "backend",
  "severity": "CRITICAL",
  "error_message": "Connection timeout on port 5432",
  "stack_trace": "Traceback...",
  "occurred_at": "2026-06-04T13:20:00Z",
  "correlation_id": "req_abc123",
  "tags": ["backend", "postgres", "timeout"],
  "metadata": {
    "region": "eu-central-1",
    "release": "2026.06.04"
  }
}
```

### Constraints:
1. `project_key` (string, required): Lowercase, alphanumeric, and dash (`-`) symbols only.
2. `occurred_at` (datetime, required): Must be a valid UTC ISO 8601 datetime format.
3. `severity` (string, required): Must match one of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
4. `correlation_id` (string, required): Crucial for trace tracking. If missing in intake requests, it will be automatically generated as `uuid` by the intake middleware, but incoming clients should provide one.
5. `error_message` (string, required): Non-empty description of the error.

## Consequences
- Guarantees multi-tenant and multi-project capabilities for BilgeAPI from day one.
- Standardizes ingestion pipeline structure across any adapter.
