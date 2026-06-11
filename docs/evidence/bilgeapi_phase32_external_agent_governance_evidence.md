# Phase 32: External Agent Governance — Evidence Report

Generated at: `2026-06-11T20:20:53.834021+00:00`
Latest Commit: `3af2d974cc779ec9e144a17f0e4f401fa7f42041`
Branch Tags: `bilgeapi-phase32-external-agent-governance-sealed`

---

## 1. E2E Verification Workflow Status

| Verification Step | Target | Status | Result Detail |
| :--- | :--- | :--- | :--- |
| **Capability Seeding** | verifier_agent | PASSED | Seeded successfully |
| **Sandbox Execution** | E:\ai_company_faz12.1\runtime\recovery\e2e_artifact.py | PASSED | Hash: `b61ca9feff72006dc659080263e5232f2516f8e4a87fc84c8a8acfde15c5a337` |
| **Promotion Request** | promo-d023fc49917d | PASSED | Status: `PENDING_APPROVAL` (Score: 1.0) |
| **Policy Simulation** | Rules Check | PASSED | Decision: `ALLOW` (Score: 15.0) |
| **Approve & Execute** | Isolated Bundle | PASSED | Status: `PROMOTED` (Msg: Promotion completed successfully.) |
| **Ledger Proof Chain** | Governance Proofs | PASSED | Logged 6 immutable events |

---

## 2. Policy Risk Score Thresholds

```text
0 - 24   → LOW (Decision: ALLOW)
25 - 49  → MEDIUM (Decision: ALLOW / Review)
50 - 74  → HIGH (Decision: HUMAN_GATE_REQUIRED)
75 - 100 → CRITICAL (Decision: BLOCK)
```

**Simulation Hash Sealed:** `28cd26961da3d895fefc14f2f7fddb97ef194c93f2ea79176055f4b7555efa78`

---

## 3. Git Repository Status

```text
M agents/ceo_agent/__pycache__/ceo_graph.cpython-313.pyc
 M apps/bilgeapi/main.py
 M apps/bilgeapi/repositories/interface.py
 M apps/bilgeapi/repositories/memory.py
 M apps/bilgeapi/repositories/postgres.py
 M apps/bilgeapi/routers/catalog.py
 M apps/bilgeapi/routers/deps.py
 M apps/bilgeapi/services/improvement.py
 M apps/bilgeapi/services/pr_verification.py
 M apps/bilgeapi/services/self_healing.py
 M apps/bilgeapi/startup.py
 M apps/public_api/__pycache__/main.cpython-312.pyc
 M apps/public_api/__pycache__/main.cpython-313.pyc
 M apps/public_api/__pycache__/main.cpython-314.pyc
 M celerybeat-schedule
 M config/policies.json
 M configs/emergency_policy.yaml
 M cortex_local_v2.db
 M docs/evidence/bilgeapi_phase15_live_smoke.md
 M docs/evidence/bilgeapi_phase18_migration_verification.md
 M libs/__pycache__/config.cpython-312.pyc
 M libs/__pycache__/config.cpython-313.pyc
 M libs/__pycache__/config.cpython-314.pyc
 M libs/db/__pycache__/session.cpython-312.pyc
 M libs/db/__pycache__/session.cpython-313.pyc
 M libs/db/__pycache__/session.cpython-314.pyc
 M libs/db/migrations/alembic/versions/__pycache__/0003_standardize_status_names.cpython-313.pyc
 M libs/db/migrations/alembic/versions/__pycache__/0004_ceo_and_router_tables.cpython-313.pyc
 M libs/db/models/__init__.py
 M libs/db/models/__pycache__/__init__.cpython-312.pyc
 M libs/db/models/__pycache__/__init__.cpython-313.pyc
 M libs/db/models/__pycache__/__init__.cpython-314.pyc
 M libs/db/models/__pycache__/repair_models.cpython-312.pyc
 M libs/db/models/__pycache__/repair_models.cpython-313.pyc
 M libs/db/models/__pycache__/repair_models.cpython-314.pyc
 M libs/db/models/__pycache__/ui_repair_models.cpython-312.pyc
 M libs/db/models/__pycache__/ui_repair_models.cpython-313.pyc
 M libs/db/models/__pycache__/ui_repair_models.cpython-314.pyc
 M libs/db/repositories/__pycache__/governor_outcome_repository.cpython-313.pyc
 M libs/db/repositories/__pycache__/governor_outcome_repository.cpython-314.pyc
 M libs/db/session.py
 M libs/infra/__pycache__/lifespan.cpython-312.pyc
 M libs/infra/__pycache__/lifespan.cpython-313.pyc
 M libs/infra/__pycache__/lifespan.cpython-314.pyc
 M libs/infra/__pycache__/router_registry.cpython-312.pyc
 M libs/infra/__pycache__/router_registry.cpython-313.pyc
 M libs/infra/__pycache__/router_registry.cpython-314.pyc
 M libs/llm/__pycache__/model_orchestrator.cpython-312.pyc
 M libs/llm/__pycache__/model_orchestrator.cpython-313.pyc
 M libs/llm/__pycache__/model_orchestrator.cpython-314.pyc
 M libs/mesh/__pycache__/state_fabric.cpython-313.pyc
 M libs/mesh/__pycache__/state_fabric.cpython-314.pyc
 M libs/queue_abstractions/job_queue.py
 M libs/workflow/__pycache__/engine.cpython-312.pyc
 M libs/workflow/__pycache__/engine.cpython-314.pyc
 M libs/workflow/__pycache__/persistence.cpython-312.pyc
 M libs/workflow/__pycache__/persistence.cpython-314.pyc
 M pytest_output.txt
 M repair_outputs/release_readiness/latest_report.json
 M requirements.txt
 M runtime/data/cortex_local.db
 D runtime/data/cortex_local.db-journal
 M runtime/data/cortex_local_v2.db
 M runtime/data/cortex_local_v2.db-shm
 M runtime/data/cortex_local_v2.db-wal
 M services/auth/__pycache__/jwt_auth.cpython-312.pyc
 M services/auth/__pycache__/jwt_auth.cpython-313.pyc
 M services/auth/__pycache__/jwt_auth.cpython-314.pyc
 M services/auth/__pycache__/router.cpython-312.pyc
 M services/auth/__pycache__/router.cpython-313.pyc
 M services/auth/__pycache__/router.cpython-314.pyc
 M services/observability/__pycache__/memory_governor.cpython-312.pyc
 M services/observability/__pycache__/memory_governor.cpython-313.pyc
 M services/observability/__pycache__/memory_governor.cpython-314.pyc
 M services/orchestration/__pycache__/trust_governor.cpython-312.pyc
 M services/orchestration/__pycache__/trust_governor.cpython-313.pyc
 M services/orchestration/__pycache__/trust_governor.cpython-314.pyc
 M services/orchestration/agi/operational/__pycache__/tool_executor.cpython-312.pyc
 M services/orchestration/agi/operational/__pycache__/tool_executor.cpython-313.pyc
 M services/orchestration/agi/operational/__pycache__/tool_executor.cpython-314.pyc
 M services/orchestration/application/__pycache__/governance.cpython-313.pyc
 M services/orchestration/application/__pycache__/governance.cpython-314.pyc
 M services/orchestration/application/__pycache__/sovereign_cortex.cpython-313.pyc
 M services/orchestration/application/__pycache__/sovereign_cortex.cpython-314.pyc
 M services/orchestration/ceo/__pycache__/engine.cpython-313.pyc
 M services/orchestration/ceo/__pycache__/engine.cpython-314.pyc
 M services/orchestration/ceo/__pycache__/repair_bridge.cpython-313.pyc
 M services/orchestration/ceo/__pycache__/repair_bridge.cpython-314.pyc
 M services/orchestration/fleet/__pycache__/fleet_scheduler.cpython-313.pyc
 M services/repair/__pycache__/mini_swe_adapter.cpython-312.pyc
 M services/repair/__pycache__/mini_swe_adapter.cpython-313.pyc
 M services/repair/__pycache__/mini_swe_adapter.cpython-314.pyc
 M services/repair/__pycache__/patch_tournament.cpython-313.pyc
 M services/repair/__pycache__/pr_agent_adapter.cpython-312.pyc
 M services/repair/__pycache__/pr_agent_adapter.cpython-313.pyc
 M services/repair/__pycache__/pr_agent_adapter.cpython-314.pyc
 M services/repair/__pycache__/release_readiness.cpython-313.pyc
 M services/repair/__pycache__/sandbox_executor.cpython-313.pyc
 M services/repair/__pycache__/sandbox_executor.cpython-314.pyc
 M services/repair/__pycache__/stagehand_adapter.cpython-312.pyc
 M services/repair/__pycache__/stagehand_adapter.cpython-313.pyc
 M services/repair/__pycache__/stagehand_adapter.cpython-314.pyc
 M services/repair/__pycache__/ui_evidence_runner.cpython-312.pyc
 M services/repair/__pycache__/ui_evidence_runner.cpython-313.pyc
 M services/repair/__pycache__/ui_evidence_runner.cpython-314.pyc
 M services/ui_repair/__pycache__/autonomous_red_team_agent.cpython-312.pyc
 M services/ui_repair/__pycache__/autonomous_red_team_agent.cpython-313.pyc
 M services/ui_repair/__pycache__/autonomous_red_team_agent.cpython-314.pyc
 M services/ui_repair/__pycache__/enterprise_readiness_assessor.cpython-312.pyc
 M services/ui_repair/__pycache__/enterprise_readiness_assessor.cpython-313.pyc
 M services/ui_repair/__pycache__/enterprise_readiness_assessor.cpython-314.pyc
 M services/ui_repair/__pycache__/external_tool_governance_router.cpython-312.pyc
 M services/ui_repair/__pycache__/external_tool_governance_router.cpython-313.pyc
 M services/ui_repair/__pycache__/external_tool_governance_router.cpython-314.pyc
 M services/ui_repair/__pycache__/final_integration_auditor.cpython-312.pyc
 M services/ui_repair/__pycache__/final_integration_auditor.cpython-313.pyc
 M services/ui_repair/__pycache__/final_integration_auditor.cpython-314.pyc
 M services/ui_repair/__pycache__/finops_recommendation_engine.cpython-312.pyc
 M services/ui_repair/__pycache__/finops_recommendation_engine.cpython-313.pyc
 M services/ui_repair/__pycache__/finops_recommendation_engine.cpython-314.pyc
 M services/ui_repair/__pycache__/global_slo_watcher.cpython-312.pyc
 M services/ui_repair/__pycache__/global_slo_watcher.cpython-313.pyc
 M services/ui_repair/__pycache__/global_slo_watcher.cpython-314.pyc
 M services/ui_repair/__pycache__/graph_edge_inferencer.cpython-312.pyc
 M services/ui_repair/__pycache__/graph_edge_inferencer.cpython-313.pyc
 M services/ui_repair/__pycache__/graph_edge_inferencer.cpython-314.pyc
 M services/ui_repair/__pycache__/graph_node_extractor.cpython-312.pyc
 M services/ui_repair/__pycache__/graph_node_extractor.cpython-313.pyc
 M services/ui_repair/__pycache__/graph_node_extractor.cpython-314.pyc
 M services/ui_repair/__pycache__/identity_governance_router.cpython-312.pyc
 M services/ui_repair/__pycache__/identity_governance_router.cpython-313.pyc
 M services/ui_repair/__pycache__/identity_governance_router.cpython-314.pyc
 M services/ui_repair/__pycache__/knowledge_graph_builder.cpython-312.pyc
 M services/ui_repair/__pycache__/knowledge_graph_builder.cpython-313.pyc
 M services/ui_repair/__pycache__/knowledge_graph_builder.cpython-314.pyc
 M services/ui_repair/__pycache__/policy_regression_verifier.cpython-312.pyc
 M services/ui_repair/__pycache__/policy_regression_verifier.cpython-313.pyc
 M services/ui_repair/__pycache__/policy_regression_verifier.cpython-314.pyc
 M services/ui_repair/__pycache__/release_readiness_checker.cpython-312.pyc
 M services/ui_repair/__pycache__/release_readiness_checker.cpython-313.pyc
 M services/ui_repair/__pycache__/release_readiness_checker.cpython-314.pyc
 M services/ui_repair/__pycache__/resiliency_mesh_router.cpython-312.pyc
 M services/ui_repair/__pycache__/resiliency_mesh_router.cpython-313.pyc
 M services/ui_repair/__pycache__/resiliency_mesh_router.cpython-314.pyc
 M services/ui_repair/__pycache__/router.cpython-312.pyc
 M services/ui_repair/__pycache__/router.cpython-313.pyc
 M services/ui_repair/__pycache__/router.cpython-314.pyc
 M services/ui_repair/__pycache__/schemas.cpython-312.pyc
 M services/ui_repair/__pycache__/schemas.cpython-313.pyc
 M services/ui_repair/__pycache__/schemas.cpython-314.pyc
 M services/ui_repair/__pycache__/security_posture_manager.cpython-313.pyc
 M services/ui_repair/__pycache__/security_posture_manager.cpython-314.pyc
 M services/ui_repair/__pycache__/service.cpython-312.pyc
 M services/ui_repair/__pycache__/service.cpython-313.pyc
 M services/ui_repair/__pycache__/service.cpython-314.pyc
 M services/ui_repair/__pycache__/sovereign_identity_registry.cpython-312.pyc
 M services/ui_repair/__pycache__/sovereign_identity_registry.cpython-313.pyc
 M services/ui_repair/__pycache__/sovereign_identity_registry.cpython-314.pyc
 M services/ui_repair/__pycache__/stagehand_adapter.cpython-313.pyc
 M services/ui_repair/__pycache__/system_smoke_test_runner.cpython-312.pyc
 M services/ui_repair/__pycache__/system_smoke_test_runner.cpython-313.pyc
 M services/ui_repair/__pycache__/system_smoke_test_runner.cpython-314.pyc
 M services/workflow_api/__pycache__/ceo_router.cpython-313.pyc
 M services/workflow_api/__pycache__/ceo_router.cpython-314.pyc
 M services/workflow_api/__pycache__/governance_router.cpython-312.pyc
 M services/workflow_api/__pycache__/governance_router.cpython-313.pyc
 M services/workflow_api/__pycache__/governance_router.cpython-314.pyc
 M services/workflow_api/__pycache__/governor_router.cpython-312.pyc
 M services/workflow_api/__pycache__/governor_router.cpython-313.pyc
 M services/workflow_api/__pycache__/governor_router.cpython-314.pyc
 M services/workflow_api/__pycache__/health_router.cpython-312.pyc
 M services/workflow_api/__pycache__/health_router.cpython-313.pyc
 M services/workflow_api/__pycache__/health_router.cpython-314.pyc
 M services/workflow_api/__pycache__/main.cpython-313.pyc
 M services/workflow_api/__pycache__/main.cpython-314.pyc
 M services/workflow_api/__pycache__/repair_lab_router.cpython-312.pyc
 M services/workflow_api/__pycache__/repair_lab_router.cpython-313.pyc
 M services/workflow_api/__pycache__/repair_lab_router.cpython-314.pyc
 M tests/chaos/__pycache__/test_region_partition.cpython-313-pytest-8.3.5.pyc
 M tests/chaos/__pycache__/test_region_partition.cpython-314-pytest-9.0.2.pyc
 M tests/governance/__pycache__/conftest.cpython-314-pytest-9.0.2.pyc
 M tests/integration/__pycache__/test_ceo_repair_bridge.cpython-313-pytest-8.3.5.pyc
 M tests/integration/__pycache__/test_ceo_repair_bridge.cpython-314-pytest-9.0.2.pyc
 M tests/integration/__pycache__/test_ceo_stagehand_diagnostic_api.cpython-313-pytest-8.3.5.pyc
 M tests/integration/__pycache__/test_repair_lab_draft_pr_api.cpython-313-pytest-8.3.5.pyc
 M tests/integration/__pycache__/test_repair_lab_human_gate_api.cpython-313-pytest-8.3.5.pyc
 M tests/integration/__pycache__/test_repair_lab_learning_memory_api.cpython-313-pytest-8.3.5.pyc
 M tests/integration/__pycache__/test_repair_lab_release_readiness_api.cpython-313-pytest-8.3.5.pyc
 M tests/integration/__pycache__/test_repair_lab_tournament_api.cpython-313-pytest-8.3.5.pyc
 M tests/integration/__pycache__/test_self_repair_artifact_flow.cpython-313-pytest-8.3.5.pyc
 M tests/repair/__pycache__/test_pr_agent_adapter.cpython-313-pytest-8.3.5.pyc
 M tests/repair/__pycache__/test_pr_agent_adapter.cpython-314-pytest-9.0.2.pyc
 M tests/repair/__pycache__/test_stagehand_diagnostic_mapping.cpython-313-pytest-8.3.5.pyc
 M tests/ui_repair/__pycache__/test_cognitive_integrity.cpython-313-pytest-8.3.5.pyc
 M tests/ui_repair/__pycache__/test_cognitive_integrity.cpython-314-pytest-9.0.2.pyc
 M tests/ui_repair/__pycache__/test_resiliency_mesh.cpython-313-pytest-8.3.5.pyc
 M tests/ui_repair/__pycache__/test_resiliency_mesh.cpython-314-pytest-9.0.2.pyc
 M tests/unit/bilgeapi/test_improvements.py
 M tests/unit/bilgeapi/test_pr_verification.py
 M tests/unit/bilgeapi/test_self_healing.py
?? .agents/external/
?? .coverage
?? apps/bilgeapi.rar
?? apps/bilgeapi/schemas/skills.py
?? apps/bilgeapi/services/skill_check_service.py
?? apps/bilgeapi/services/skill_registry.py
?? apps/refine_control_plane/src/app/proof/snapshots/[id]/
?? coverage.xml
?? docs/SKILL_POLICY.md
?? docs/agent-skills/
?? file
?? runtime/pytest_unit_phase15_20.out
?? runtime/recovery/
?? tests/ui_repair/test_patch.patch
?? tests/ui_repair/test_patch_hash.patch
?? tests/unit/bilgeapi/test_skills_catalog.py
?? tests/unit/bilgeapi/test_skills_check.py
?? tests/unit/bilgeapi/test_skills_router.py
```

---

## 4. Test Verification Summary

* `test_agent_registry_sandbox_phase32b.py`: **PASSED**
* `test_agent_promotion_gate_phase32c.py`: **PASSED**
* `test_agent_policy_simulator_phase32e.py`: **PASSED**
* `test_phase27_ops_console_static.py`: **PASSED**
* `Frontend Production Build (refine_control_plane)`: **PASSED / SUCCESS**

---

**Release Gate Decision:** **GO / PASSED (Score: 100.00)**
**Final Sealed Tag:** `bilgeapi-phase32-external-agent-governance-sealed`
