# Implementation Plan - BilgeAPI Faz 27: Admin UI / Ops Console

Bu faz, Faz 14-26 arasinda kurulan BilgeAPI operasyon altyapisini tek bir operator panelinden yonetilebilir hale getirir.

## Goal

`apps/refine_control_plane` icinde `/bilgeapi-ops` route'u olusturularak su alanlar tek yuzeye tasinir:

- API Keys
- Quotas
- Research Requests
- Improvement Proposals
- Draft PRs
- Sandbox Verifications
- Reviewer Feedback
- Patch Revisions
- Release Gate Status
- Audit Trail

## Architecture

```text
apps/refine_control_plane /bilgeapi-ops
  -> Next rewrite /bilgeapi/*
  -> BilgeAPI http://127.0.0.1:8100/*
  -> Existing DB-backed BilgeAPI services
```

Backend'e yeni davranis eklemek bu fazin ana hedefi degildir. Mevcut endpoint'ler client aggregation ile panele baglanir.

## Proposed Changes

1. `apps/refine_control_plane/next.config.ts`
   - `/bilgeapi/:path*` rewrite eklenir.
   - Varsayilan hedef `http://127.0.0.1:8100`.

2. `apps/refine_control_plane/src/lib/bilgeapiOpsClient.ts`
   - BilgeAPI admin/operator API client katmani.
   - `X-API-Key` header destegi.
   - API key create/list/revoke/quota usage.
   - research/proposal/draft-pr/verification/feedback/revision/release/audit client fonksiyonlari.
   - `plaintext_key` sadece create response icin tutulur, action log tarafinda redakte edilir.

3. `apps/refine_control_plane/src/app/bilgeapi-ops/page.tsx`
   - Dashboard summary.
   - API key create/revoke/quota paneli.
   - Research/evidence/proposal paneli.
   - Draft PR + sandbox verification paneli.
   - Reviewer feedback + patch revision paneli.
   - Release gate + audit trail paneli.

4. Navigation
   - `apps/refine_control_plane/src/app/providers.tsx` icinde resource kaydi.
   - `apps/refine_control_plane/src/components/Sidebar.tsx` icinde `bilgeapi-ops` menu entry.

## Safety Rules

- UI merge/deploy/apply yapmaz.
- Draft PR ve patch revision akislari sadece mevcut BilgeAPI endpoint'lerini tetikler.
- Plaintext API key listelerde, audit/action log'da veya quota ekraninda gosterilmez.
- BilgeAPI operator key browser session scope'unda tutulur; clear aksiyonu ile silinir.

## Verification Plan

- Static contract test:
  `py -3.13 -m pytest tests/unit/bilgeapi/test_phase27_ops_console_static.py -q`
- Frontend build:
  `npm run build` in `apps/refine_control_plane`
- BilgeAPI regression:
  `py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing -q`
- OpenAPI export:
  `py -3.13 scripts/export_bilgeapi_openapi.py`
- Release gate:
  `py -3.13 scripts/run_release_gate.py`
- Docker/live smoke:
  `docker compose up -d bilgeapi`
  `py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001`

---

# Implementation Plan — Phase 32: External Repo Intake & Governance

This plan outlines the integration of external developer-agent repositories and utilities (`SWE-agent`, `SWE-ReX`, `PR-Agent/Qodo`, `Stagehand`, `OpenHands`, and architectural patterns from `GitHub Copilot`) into the Sovereign AGI self-repair and governance pipeline.

We adhere strictly to the **governance-first principle**: **CEO Finding → Repair Case → External Agent Adapter → Artifact → Verifier/Risk → Human Gate → Draft PR/Learning Memory**.

---

## 2026-06-03 P0 Control-Plane Route Repairs

### Scope
- `governor/drills`: hydration-safe tarih render ve row contract düzeltmesi
- `governance/proposals` / `policy-proposals`: `policy_proposals` schema drift toleransı
- `self-tuning`: `repair_lab` tuning endpoint path hizalaması
- `governor/scorecard`: enum drift (`GovernorDecisionQuality` vs `GovernorOutcomeQuality`) düzeltmesi
- `governor/proof/snapshots/[id]`: detail endpoint, frontend path ve inspect akışı düzeltmesi

### Acceptance
1. Hedef sayfalar `3100` üstünde açılırken `page_error` üretmemeli.
2. `GET /api/v1/governance/proposals` eski `policy_proposals` şemasıyla da `200` dönmeli.
3. `GET /api/v1/governance/governor/scorecard` `GovernorDecisionQuality.CORRECT` verisini doğru saymalı.
4. `GET /api/v1/governance/governor/proof/snapshots/{id}` hem persisted hem `derived-local-proof-snapshot` için çalışmalı.
5. Canlı audit tekrarında P0 route’lar temizlenmeli.

### Test Strategy
- Backend regression tests:
  - proposals schema drift fallback
  - governor scorecard accuracy aggregation
  - proof snapshot detail (persisted + derived)
- Frontend/runtime verification:
  - `npm run build`
  - hedef route’lara canlı GET/smoke
  - `runtime/live-test/page_audit.py` tekrar koşumu

---

## Scope

### In-Scope
1. **Catalog Definition**: Creation of `configs/external_agent_catalog.yaml` to specify metadata (name, repo_url, pinned_commit, license, purpose, risk_level, allowed_modes, forbidden_actions).
2. **Adapter Layer**: Extending `services/repair/external_repo_integrations.py` to act as the single source of truth for loading, verifying, and routing external tools.
3. **Safety & Sandbox Guardrails**: Ensuring external agents are executed only in safe environments, outputs are compiled as clean artifacts, and risk assessments are applied.
4. **Human Gate Enforcement**: Requiring operator approval for any external patch candidates before they can be merged or pushed.
5. **Testing/Verification**: Comprehensive tests ensuring catalog parsing, safety controls, and mock/real adapter flows execute correctly.

### Out-of-Scope (This Phase)
- Automatic merging/pushing of unreviewed patches without operator verification.
- Direct vendor-in of external code without safe adaptation wrappers.
- Executing active agents with direct access to production secrets/DBs.
- Bypassing the Human Gate.

---

## Architectural Flow & Pipeline

```mermaid
graph TD
    A[CEO Finding / Incident / Test Fail] --> B[Build Repair Case]
    B --> C[Select Adapter from Catalog]
    C --> D{Verify License & Risk}
    D -- Safe --> E[Execute in Sandbox / Simulation]
    D -- Forbidden --> F[Block & Log Alert]
    E --> G[Generate Patch / Diagnostic Artifact]
    G --> H[Verifier Mesh & Risk Scoring]
    H --> I[Human Gate Operator Review]
    I -- Approved --> J[Prepare Draft PR & Persist Memory]
    I -- Rejected --> K[Log Rejection & Update Learning Memory]
```

---

## Action Plan

### Step 1: Catalog Creation (`configs/external_agent_catalog.yaml`)
Create the catalog with strict governance fields:
- Pinned commit / version
- License compliance check (e.g., Apache-2.0, MIT)
- Allowed modes (reference_only, local_adapter, sandbox_runner, review_gate, experimental)
- Forbidden actions (direct_git_push, production_secrets_read, etc.)

### Step 2: Extend Orchestrator/Integrations Adapter (`services/repair/external_repo_integrations.py`)
- Add a parser for `external_agent_catalog.yaml` using PyYAML.
- Add a validation function `validate_agent_execution(agent_name, requested_mode)` that checks if the request complies with the catalog's `allowed_modes` and `risk_level`.
- Implement safety checker to block any actions in `forbidden_actions`.

### Step 3: Update and Align Individual Adapters
Ensure each adapter has a unified API and maps to the catalog properties:
- `swe_rex_adapter.py`: Sandboxed command runner and execution coordinator.
- `stagehand_adapter.py`: UI diagnosis, Playwright trace collection, visual assertion runner.
- `pr_agent_adapter.py`: Patch review and risk rating.
- `mini_swe_adapter.py` / `swe_agent_adapter.py`: Issue-to-patch code generation.
- Add a mock/placeholder adapter logic for heavier tools like `OpenHands` and `GitHub Copilot` (reference_only / experimental).

### Step 4: Integration in Self-Repair Workflow
Connect the catalog validation and adapters to `services/repair/repair_orchestrator.py` during `generate_patch_candidate_step`.

### Step 5: Verification & Testing
- Write unit tests in `tests/repair/test_external_repo_governance.py` to assert:
  - Valid catalog loading and schema compliance.
  - Rejection of unauthorized/forbidden modes or actions.
  - Flow integrity from Case Builder to Risk Score to Human Gate.
- Run tests and fix any issues iteratively using standard python testing (`pytest`).

---

## Phase 3 — Repair Case → TaskFlow v2 Run Bridge

### Purpose
Bridges the generated `repair_outputs/{incident_id}/repair_case.json` artifact to a live `self_repair` TaskFlow run, persists run details, and updates the CEO finding status to `TASKFLOW_RUNNING` or `REPAIR_CASE_CREATED` depending on the `auto_start` configuration.

### Scope
- **In-Scope**:
  - Deserialize and validate `repair_case.json` securely.
  - Map `RepairCaseInput` and finding details to a valid registered `self_repair` workflow run (`Project` + `SubTask` records).
  - Enqueue the workflow job asynchronously using `job_queue.enqueue("run_project", ...)`.
  - Handle `auto_start=True` and `auto_start=False` logic correctly:
    - If `auto_start=True`: status updates to `TASKFLOW_RUNNING` or `TASKFLOW_QUEUED` (and job enqueued).
    - If `auto_start=False`: status updates to `REPAIR_CASE_CREATED` (and job not enqueued).
  - Persist metadata regarding the started run to `repair_outputs/{incident_id}/taskflow_run.json`.
  - Detailed integration tests in `tests/integration/test_ceo_repair_taskflow_bridge.py`.

- **Out-of-Scope**:
  - Real execution of external subprocesses (wrapped inside the adapters).
  - Automated pull request merging/pushing.

### Implementation Steps
1. **Update `services/orchestration/ceo/repair_bridge.py`**:
   - Make `start_self_repair_from_repair_case` an `async` function.
   - Inject dependencies/repositories required for workflow project creation and database sessions.
   - Map `RepairCaseInput` variables to the `Project` model context `execution_context` (standardizing all required keys like `incident_id`, `source="ceo_finding"`, etc.).
   - Dispatch to `job_queue` if `auto_start=True`.
   - Write output metadata file `taskflow_run.json` containing the started run's parameters under the incident folder.
2. **Update Endpoint `POST /api/v1/ceo/findings/{finding_id}/repair-case`**:
   - Ensure it calls the updated `async` bridge function.
   - Return structured response including the created workflow ID/job details.
3. **Integration Tests (`tests/integration/test_ceo_repair_taskflow_bridge.py`)**:
   - Implement comprehensive tests for `auto_start=True` (confirming project DB creation, enqueuing, and `taskflow_run.json` artifact) and `auto_start=False`.
   - Add resilience tests to guarantee graceful handling of enqueuing/dispatch failures without deleting the compiled case.

---

## Success Criteria & Definition of Done
1. `external_agent_catalog.yaml` is fully specified and validates under yaml loader.
2. `external_repo_integrations.py` is capable of loading and checking safety rules of all candidates.
3. Patch generation using an adapter is properly intercepted by the Risk Scoring & Verifier Mesh.
4. Test suite coverage is >80% for new integration code.
5. Zero modifications are made to the live repository without Human Gate approval.
6. A live TaskFlow workflow project is programmatically created, enqueued, and tracked correctly inside the database for every `auto_start=True` repair case request.

---

## Phase 5 — Human Gate Decision Center

### Purpose
Transition the `approval_gate` taskflow step from a passive wait state into a strict, evidence-driven human-in-the-loop gate. All high-risk runs require structured operator sign-off containing rationale, risk acknowledgment, target candidate ID, and a valid rollback plan reference.

### Scope
* **In-Scope**:
  * Solidify the `human_gate_decision.json` schema and enforce validation rules (non-empty rationale, candidate existence, high-risk acknowledgment, rollback plan validation, blocking policy-denied or sandbox-failed patches).
  * Persist every decision with non-repudiable audit logs written sequentially to `human_gate_audit.jsonl`.
  * Expose dedicated endpoints for querying and submitting decisions:
    * `GET /api/v1/repair-lab/runs/{run_id}/human-gate`
    * `POST /api/v1/repair-lab/runs/{run_id}/human-gate/decision`
  * Integrate the gate directly into `self_repair_v1` workflow step logic.
  * Implement rigorous unit/contract and API integration tests.

### Implementation Steps
1. **Model & Validation Core** (`services/repair/human_gate.py`):
   * Define enum-based types for decisions, operator actions, and status.
   * Add validator functions to enforce:
     * Non-empty operator rationale.
     * Candidate inclusion inside the candidate list.
     * Mandatory `risk_acknowledgement` if risk score > `risk_threshold`.
     * Mandatory `rollback_plan_ref` if `rollback_required` is true.
     * Safety blocks preventing approval of `policy denied` or `sandbox failed` candidates, or if missing critical verifier results.
   * Implement `record_human_gate_decision` to load existing schemas, validate the request, write the decision to `human_gate_decision.json`, and append JSON lines to `human_gate_audit.jsonl`.
2. **Workflow Engine Adaptation** (`services/taskflow/tasks/` or `self_repair_v1` step handlers):
   * Update `approval_gate` handler to halt execution if `risk_score > threshold` and no decision artifact exists.
   * Update `prepare_draft_pr` handler to block if `human_gate_decision.status` is not `APPROVED` or `DRAFT_PR_ONLY`.
3. **Router Endpoints** (`services/workflow_api/repair_lab_router.py`):
   * Add `GET /runs/{run_id}/human-gate` and `POST /runs/{run_id}/human-gate/decision`.
4. **Testing Suites**:
   * Create `tests/repair/test_human_gate_decision.py` for validation constraints and audit logging.
   * Create `tests/integration/test_repair_lab_human_gate_api.py` for endpoint contract validation.
