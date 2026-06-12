# Architectural Decision Record — ADR-v1.3-multitenant-auth

* **Status:** Proposed
* **Date:** 2026-06-12
* **Decider:** AI Coding Agent (Antigravity) & Operator

---

## 1. Context

Currently, static API keys are scoped globally without tenant boundaries. As BilgeAPI matures to support multiple concurrent projects/teams, we must enforce tenant isolation at the authentication layer to prevent cross-tenant data leaks and allow customized rate limits.

---

## 2. Decision

We will implement tenant-bound API keys and strict RBAC scopes in v1.3.

1. **Database Schema Constraints:** Link all database-backed API keys (`ApiKeyModel`) to a specific `tenant_id`.
2. **Granular Permissions Scopes:**
   * Support role mappings (`ADMIN`, `OPERATOR`, `METERING_READONLY`).
   * Limit actions: restrict `OPERATOR` keys from modifying capability toggles.
3. **Tenant-Aware Query Filters:** Automatically inject the authenticated `tenant_id` as a query parameter into all database repository searches for incidents and runs.

---

## 3. Consequences

* **Pros:**
  * Strict multi-tenant isolation.
  * Blocks lateral movement (cross-tenant access) even if keys are leaked.
* **Cons:**
  * Increases database query complexity.
