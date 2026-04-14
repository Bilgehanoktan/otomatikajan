# Project Isolation & Multitenancy Model

This document outlines the Sovereign AGI project isolation strategy (Faz 14 P2).

## Core Principles
1. **Strict Boundary Enforcement:** No project should be able to access secrets or data from another project.
2. **Resource Quotas:** Budget limits and rate limits are enforced per project ID.
3. **Policy Overrides:** Specific projects can have stricter autonomy or model limits.

## Implementation Detail
- **Service Layer:** `ProjectScope` service manages context-aware policy loading.
- **Context Management:** `contextvars` are used to propagate `project_id` throughout the execution stack.
- **Secret Scoping:** API keys are retrieved via `ProjectSecretProvider` which prevents cross-project leakage.

## Directory Structure
- `configs/project_policies/default.yaml`: Base limits.
- `DATA_DIR/configs/project_policies/{UUID}.yaml`: Project-specific overrides.

## Future Plans
- **Database RLS:** Implementation of Postgres Row Level Security for absolute data isolation.
- **Project-Level HSM:** Hardware Security Module integration for enterprise tenants.
