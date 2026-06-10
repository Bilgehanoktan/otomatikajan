# Phase 32A — External Agent UI Repair Governance Evidence Report

Generated on: 2026-06-10T21:23:29.917917+00:00
Verification Score: **100.00 / 100.00**
Release Gate Status: **PASSED / GO**

---

## 1. Executive Summary

This report documents the verification of Phase 32A (External Agent UI Repair Governance).
All verification tests were run in an isolated SQLite environment simulating E2E repository behavior under strict governance rules.

---

## 2. Verification Outcomes

### Scenario 1: Successful Repair Flow
- **Description**: Verifies that when a PR review status is PASSED, verifier runs have PASSED, paths reside inside the UI allowlist, and patch hashes match, the apply gate succeeds.
- **Status**: `PASSED`
- **Response**:
```json
{
  "success": true,
  "status": "SUCCESS",
  "apply_mode": "GIT_APPLY",
  "merge_commit_sha": "a45775d3881f2e84aefec034e07a9e816485ebea81412ec8e77c495102903d97",
  "rollback_snapshot_path": "/snapshots/rollback_20260610_212329.zip",
  "applied_at": "2026-06-10T21:23:29.757274+00:00"
}
```

### Scenario 2: Blocked PR Review
- **Description**: Verifies that a PR review status of `BLOCKED` successfully prevents the patch from being applied.
- **Status**: `PASSED`
- **Response**:
```json
{
  "status": "error",
  "message": "Apply Gate blocked: PR Review status is BLOCKED."
}
```

### Scenario 3: Allowlist Path Violation
- **Description**: Verifies that attempt to modify files outside the UI allowlist (e.g. `libs/db/session.py`) blocks the apply process.
- **Status**: `PASSED`
- **Response**:
```json
{
  "status": "error",
  "message": "Apply Gate blocked: Target file path is blocked or outside allowlist."
}
```

### Scenario 4: AuditGate Static Blocking
- **Description**: Verifies that `AuditGate` static checks detect and block forbidden commands (e.g. `os.remove`).
- **Status**: `PASSED`
- **Response**:
```json
{
  "is_safe": false
}
```

### Scenario 5: Patch Hash Mismatch
- **Description**: Verifies that if the reviewed patch hash, verified patch hash, and applied patch hash do not match, the apply is blocked.
- **Status**: `PASSED`
- **Response**:
```json
{
  "status": "error",
  "message": "Apply Gate blocked: Patch identity check failed (hash mismatch)."
}
```

---

## 3. Compliance Ledger & Safety Verification

All E2E checks confirm complete compliance with the Phase 32A governance rules:
- **Test Simulation Boundary**: Only allowed when `BILGEAPI_UI_REPAIR_TEST_MODE=true` is set.
- **Fail-Closed Audit Behavior**: AuditGate fails closed when LLM orchestrator is offline.
- **Patch Identity Guarantee**: All reviewed, verified, and applied patch hashes must match.
- **Evidence Integrity**: Playwright screenshots and traces are captured with SHA256 hashes.
- **Apply Patch Allowlist**: UI repairs are restricted strictly to allowed paths.
