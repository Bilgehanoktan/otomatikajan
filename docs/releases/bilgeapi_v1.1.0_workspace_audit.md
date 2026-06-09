# BilgeAPI v1.1.0 Workspace Audit

## Scope

Bu audit, Faz 30 release commit'ine yalnizca release artefact'lerinin girmesini saglamak icin hazirlandi.

Release baseline:

- Baseline commit: `2069a36864270244c3714ead9c2efdc0d7ee12ea`
- Planned tag: `bilgeapi-v1.1.0`
- Migration head: `a29c4f83b2d1`

## Git State Evidence

Raw evidence files:

- `docs/releases/bilgeapi_v1.1.0/git_status_release.txt`
- `docs/releases/bilgeapi_v1.1.0/git_diff_name_only.txt`
- `docs/releases/bilgeapi_v1.1.0/git_diff_cached_name_only.txt`

## Release Commit Inclusion Policy

Faz 30 commit'ine sadece su path'ler dahil edilecek:

- `implementation_plan.md`
- `task.md`
- `walkthrough.md`
- `docs/openapi/bilgeapi_openapi.v1.1.0.json`
- `docs/releases/bilgeapi_v1.1.0_workspace_audit.md`
- `docs/releases/bilgeapi_v1.1.0_changelog.md`
- `docs/releases/bilgeapi_v1.1.0/**`

## Explicit Exclusions

Asagidaki dosya tipleri ve path'ler release commit'inden dislanacak:

- Runtime database files: `runtime/data/*.db`, `runtime/data/*.db-wal`, `runtime/data/*.db-shm`, `cortex_local_v2.db`
- Coverage/runtime byproducts: `.coverage`, `coverage.xml`, `pytest_output.txt`
- Python caches: `__pycache__/**`
- Existing unrelated staged work, including `apps/refine_control_plane/src/app/proof/snapshots/[id]/page.tsx`
- Non-BilgeAPI unrelated changes under `services/**`, `libs/**`, `config/**`, `configs/**`, `tests/ui_repair/**`, `tests/integration/**`

## Decision

Workspace genelinde unrelated dirty/staged dosyalar vardir. Bunlar Faz 30 release seal kapsaminda degildir ve final commit'e alinmayacaktir.

