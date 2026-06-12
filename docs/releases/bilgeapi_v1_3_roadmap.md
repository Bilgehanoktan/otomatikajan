# BilgeAPI v1.3.0 — Roadmap & Scoping Plan

Generated at: `2026-06-12T20:20:00Z`
Target Release: **v1.3.0**
Phase: **Phase 37 — BilgeAPI v1.3 Roadmap Planning**

---

## 1. Priority Matrix

We evaluated the candidate themes using the prioritization formula:
\[\text{Priority} = (\text{Impact} + \text{Risk Reduction}) - \text{Effort}\]

*Each scored from 1 (lowest) to 5 (highest).*

| Theme | Description | Impact | Risk Red. | Effort | Priority | Scoped |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **AST Scanner** | Structured Abstract Syntax Tree scanning for agent patches | 5 | 5 | 3 | **7** | **MVP** |
| **Metadata API** | Centralized `/v1/system/release` endpoint | 4 | 4 | 2 | **6** | **MVP** |
| **OTel Metrics** | Prometheus `/metrics` and OpenTelemetry exporter | 4 | 3 | 3 | **4** | **MVP** |
| **Multi-Tenant Auth** | Tenant-bound API keys and RBAC scopes | 4 | 3 | 4 | **3** | Backlog |
| **Agent Budgets** | Budget scheduler queue & budget limits | 3 | 3 | 4 | **2** | Backlog |
| **Dashboard UI** | Ops Dashboard monitoring cards & ledger explorer | 3 | 2 | 3 | **2** | Backlog |

---

## 2. v1.3 MVP Scope (Selected Themes)

### 1. AST-Based Skill Check Upgrade (ADR-v1.3-ast-skill-check-service)
* **Goal:** Replace regex keywords validation with syntax-aware tree parsing to prevent evasion.
* **Deliverable:** `SkillVisitor` parsing python files, logging line/column of security anomalies.

### 2. Centralized Release Metadata Service (ADR-v1.3-release-metadata-service)
* **Goal:** Centralize versioning and release context tracking.
* **Deliverable:** Endpoints `/v1/system/release` exposing commit SHA and docker build time.

### 3. OpenTelemetry Prometheus Exporter (ADR-v1.3-opentelemetry-metrics)
* **Goal:** Support standard instrumentation and metrics scraping.
* **Deliverable:** Endpoint `/metrics` exporting latencies, error counts, and database connections.

---

## 3. Non-Goals for v1.3
* Re-architecting core FastAPI router schemas.
* Porting background queue backend away from Celery/Redis.
* Deploying public tenant sign-up UIs.
