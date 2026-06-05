# ADR-003: Adapter Interfaces & Webhook Dispatch Security Rules

## Status
Approved

## Context
BilgeAPI communicates with external agents and downstream healing systems through adapters. We need a standardized contract for run-time diagnostics and dispatch mechanisms, alongside robust security measures for webhook callbacks to prevent Server-Side Request Forgery (SSRF) and other attacks.

## Decision
1. **Diagnostic & Repair Adapter Contracts**:
   - Every diagnostic engine must implement the `DiagnosticAdapter` interface:
     - `name: str`
     - `async run_diagnostic(incident: Incident) -> DiagnosticResult`
     - `async health_check() -> bool`
   - Every repair dispatch engine must implement the `RepairDispatchAdapter` interface:
     - `name: str`
     - `async dispatch_repair_request(repair_request: RepairRequest) -> WebhookDelivery`
     - `async health_check() -> bool`

2. **First-Phase Adapters**:
   - `mock_agent`: A deterministic diagnostic simulator returning structured findings and recommendations.
   - `webhook`: A secure payload sender with signature-based validation.

3. **Webhook Security Guardrails**:
   - **SSRF Prevention**: IP resolving checks to deny requests targeting localhost, loopback interfaces (`127.0.0.1`, `::1`), private IP ranges (RFC 1918 e.g., `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and link-local ranges (`169.254.169.254`).
   - **Redirect Controls**: Maximum redirects set to `0`.
   - **Timeout Policy**: Connection timeout at 3 seconds, write/read timeout at 5 seconds.
   - **Signature Verification**: Webhooks are signed using HMAC-SHA256 based on a shared secret. Payload headers include:
     - `X-BilgeAPI-Signature`: Hex signature.
     - `X-BilgeAPI-Timestamp`: Unix timestamp to prevent replay attacks (validated within a 5-minute drift window).
   - **Reliability & Retry**: Exponential backoff retry with random jitter. Maximum attempt counts set to 5 before flagging as dead-letter delivery.

## Consequences
- Ensures security when dispatching signals to arbitrary webhooks.
- Decouples API endpoints from specific diagnostic engines (mock agent, Stagehand, SWE-agent, etc.).
