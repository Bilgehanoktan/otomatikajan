# Integration Governance & Connector Capability Model

This document specifies how Sovereign AGI manages external integrations and tool safety.

## 1. Capability Registry
Every connector joined to the platform must be registered in the `CapabilityRegistry`.
- **Allowed Tools:** Sub-list of tools that the agent is allowed to invoke for a specific integration.
- **Enforcement:** The `IntegrationGuard` intercepts all tool calls and verifies them against the registry.

## 2. Standards
- **Timeout:** Default 30s for external API calls to prevent hanging workers.
- **Retries:** Exponential backoff with a maximum of 3 retries for transient errors.
- **Secret Ownership:** Secrets for connectors are scoped to the project level.

## 3. Connector Health
Managed via a dedicated panel in the Control Plane, displaying latency and error rates per integration.
