# ADR-004: Asynchronous Diagnostic Lifecycle

## Status
Approved

## Context
Diagnostic runs can be time-consuming (e.g. log analysis, system scans, running verification checks). The API contract must be designed for asynchronous operations from day one to avoid blocking HTTP connections and timing out.

## Decision
1. **Lifecycle States**:
   - `QUEUED`: Job is created and waiting to be processed by an adapter.
   - `RUNNING`: Job is currently being executed by the diagnostic adapter.
   - `COMPLETED`: Diagnostic runs completed successfully, compiling findings and recommendations.
   - `FAILED`: Diagnostic execution encountered an error.

2. **Triggering Endpoint**:
   - `POST /v1/incidents/{incident_id}/diagnostics`
   - Returns a `202 Accepted` status with an async tracking token:
     ```json
     {
       "diagnostic_id": "diag_abc123",
       "status": "QUEUED",
       "next_action": "CHECK_DIAGNOSTIC_STATUS"
     }
     ```

3. **Status Check & Results**:
   - `GET /v1/diagnostics/{diagnostic_id}`
   - Returns details and the diagnostic results when finished:
     ```json
     {
       "diagnostic_id": "diag_abc123",
       "status": "COMPLETED",
       "summary": "Database connection timeout detected.",
       "root_cause_hypothesis": "PostgreSQL connection pool exhaustion.",
       "confidence": 0.82,
       "risk_score": 0.35,
       "findings": [],
       "recommendations": []
     }
     ```

## Consequences
- Prevents UI/API gateway timeouts on long diagnostic steps.
- Prepares the contract for heavy LLM or sandboxed agents in later phases.
