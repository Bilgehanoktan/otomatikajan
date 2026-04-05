# Implementation Plan - Modularization of Sovereign AGI

## Overview
This plan outlines the steps for transitioning the Sovereign AGI codebase from a monolithic structure to a modular architecture based on bounded contexts.

## Objectives
- Eliminate circular dependencies.
- Clear separation between API, Worker, and Shared Packages.
- Clean up the repository root.
- Establish a single source of truth for states and schemas.

## Phase 1: Repo Sterilization (Root Cleanup) - [IN PROGRESS]
- [ ] Create missing skeleton directories (`runtime/`, `tools/`, `external/`, `docs/`).
- [ ] Move non-code assets and runtime data (DBs, logs, tmp) to `runtime/`.
- [ ] Move development tools and scripts to `tools/`.
- [ ] Move third-party and legacy assets to `external/`.
- [ ] Clean up redundant root files.

## Phase 2: Target Skeleton Setup
- [ ] Ensure all subdirectories in `apps/` and `packages/` are correctly initialized.

## Phase 3: Contracts Extraction
- [ ] Parcellate `schemas.py` into `packages/contracts/`.
- [ ] Create compatibility shims in `core/schemas.py`.

## Phase 4: Observability and Persistence
- [ ] Move `observability/` to `packages/observability/`.
- [ ] Move `db/` and migrations to `packages/persistence/`.

## Phase 5: API Entry Points
- [ ] Move `main.py` and startup logic to `apps/api/`.
- [ ] Move routers to `apps/api/routers/`.

## Phase 6: Worker Separation
- [ ] Move `tasks/` to `apps/worker/tasks/`.
- [ ] Establish `apps/worker/main.py`.

## Phase 7: Repair Engine Extraction
- [ ] Move `repair/` and `core/repair_orchestrator.py` to `packages/repair_engine/`.

## Phase 8: LLM Gateway Extraction
- [ ] Move `llm/` to `packages/llm_gateway/`.

## Phase 9: Orchestration Extraction
- [ ] Move orchestration logic from `core/` to `packages/orchestration/`.

## Phase 10: Improve / Heal / Memory
- [ ] Consolidate and move redundant improvement, healing, and memory logic.

## Phase 11: Skills and Integrations
- [ ] Move `skills/` and integrations to `packages/`.
- [ ] Clean up redundant telegram/deerflow structures.

## Phase 12: Dashboard Separation
- [ ] Move `dashboard/` to `apps/dashboard/`.

---

> [!IMPORTANT]
> All changes follow the "move + shim + test" rule to prevent system breakage.
