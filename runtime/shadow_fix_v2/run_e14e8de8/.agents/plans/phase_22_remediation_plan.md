# Phase 22 Implementation Plan — Autonomous Remediation & Compliance Auto-Fix

## 1. Overview
Phase 22 shifts the platform from detection (Phase 21) to active, governed remediation. It introduces automated finding classification, remediation planning, and an auto-fix engine that generates patches/PRs for low-risk findings while escalating critical issues to human operators.

## 2. Proposed Changes

### 2.1 Database Models (`libs/db/models/ui_repair_models.py`)
Add models to track remediation lifecycle:
- `RemediationStatus` (Enum): `PLANNED`, `WAITING_APPROVAL`, `AUTO_FIX_RUNNING`, etc.
- `RemediationType` (Enum): `POLICY_TIGHTENING`, `CONFIG_HARDENING`, etc.
- `UISecurityRemediationPlan`: The strategy to fix a specific finding.
- `UISecurityAutoFixAttempt`: Tracking the execution of a remediation plan.
- `UIComplianceFixResult`: The outcome and impact on compliance scores.
- `UISecurityRemediationEvent`: Audit trail for remediation actions.

### 2.2 Backend Services (`services/ui_repair/`)
Implement core remediation logic:
- `security_finding_classifier.py`: Assigns severity (LOW to CRITICAL) and risk levels.
- `remediation_planner.py`: Generates actionable plans based on findings.
- `compliance_autofix_engine.py`: Logic for automated fixes (policy hardening, metadata repair).
- `security_fix_orchestrator.py`: Orchestrates the full lifecycle (Plan -> Fix -> Rescan).
- `posture_rescan_service.py`: Triggers rescan after fixes to verify resolution.
- `compliance_fix_policy.py`: Enforces guardrails (e.g., no auto-fix for CRITICAL).

### 2.3 API Layer (`services/ui_repair/router.py` & `schemas.py`)
- New endpoints for managing remediation plans and attempts.
- Pydantic schemas for all new models.

### 2.4 Frontend Dashboard (`apps/refine_control_plane/`)
- New tabs in Security Posture Center:
  - **Remediation Plans**: List and detail views.
  - **Auto-Fix Attempts**: Status tracking and logs.
  - **Fix Results**: Before/after score comparisons.
  - **Residual Risks**: Tracking issues that couldn't be fully resolved.

## 3. Implementation Workflow

### Step 1: Database & Enums
1. Update `ui_repair_models.py` with new enums and tables.

### Step 2: Schemas
1. Update `schemas.py` with Pydantic V2 models.

### Step 3: Core Remediation Logic
1. Implement `SecurityFindingClassifier`.
2. Implement `RemediationPlanner`.
3. Implement `ComplianceAutoFixEngine`.
4. Implement `SecurityFixOrchestrator`.

### Step 4: API & Service Integration
1. Update `UIRepairService` and `router.py`.

### Step 5: Frontend Implementation
1. Create React components for Remediation/Fix panels.

### Step 6: Verification
1. Backend & Frontend tests.

## 4. Safety Guardrails
- **No Auto-Apply**: Production changes always require operator final approval.
- **Critical Block**: Critical findings (e.g., secret leaks) disable auto-fix engines immediately.
- **Cognitive Integrity**: All generated patches are checked for hallucinations.
