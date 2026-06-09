# Implementation Plan - BilgeAPI Faz 30: v1.1 Final Release Seal

Bu faz, Faz 14-29 arasinda olusan BilgeAPI v1.1 gelistirme hattini final release olarak muhurlenir hale getirir. Faz 30 yeni runtime ozelligi eklemez; release kaniti, OpenAPI freeze, changelog, workspace audit, checksum manifest, final commit ve tag uretir.

## Goal

BilgeAPI v1.1.0 icin tekrarlanabilir ve denetlenebilir release paketi olusturmak:

```text
Baseline commit -> Verification evidence -> OpenAPI freeze -> Changelog -> Checksum manifest -> Final commit -> Annotated tag
```

## Release Baseline

- Baseline commit: `2069a368`
- Final tag: `bilgeapi-v1.1.0`
- Migration head: `a29c4f83b2d1`
- Minimum coverage: `80%`
- Release gate target: `Score: 100.00`, `Status: PASSED`, `Warnings: 0`, `Blockers: 0`, `Decision: GO`

## Safety Rules

- Faz 30 release commit'ine unrelated dirty/staged dosyalar dahil edilmeyecek.
- Runtime database files, `.coverage`, `coverage.xml`, `pytest_output.txt`, `__pycache__`, generated local state ve eski staged dosyalar release commit'ine alinmayacak.
- Release dosyalari explicit path ile stage edilecek.
- Docker, smoke, frontend ve migration kontrolleri gecmezse final tag olusturulmayacak.
- Docker daemon veya external runtime erisilemiyorsa durum release evidence icinde acikca `BLOCKED/NOT VERIFIED` olarak kaydedilecek.

## Proposed Changes

### 1. Workspace Audit

`docs/releases/bilgeapi_v1.1.0_workspace_audit.md` olusturulacak.

Icerik:

- `git status --short`
- `git diff --name-only`
- `git diff --cached --name-only`
- unrelated dirty/staged dosya karari
- release commit'e dahil edilecek dosya listesi

### 2. OpenAPI Freeze

`py -3.13 scripts/export_bilgeapi_openapi.py` calistirilacak ve guncel spec su dosyaya kopyalanacak:

- `docs/openapi/bilgeapi_openapi.v1.1.0.json`

Freeze kontrolu:

- JSON parse edilebilir olmali.
- `/v1/improvements/*` endpointleri bulunmali.
- `/v1/review-ledger/*` endpointleri bulunmali.
- `/health` endpointi bulunmali.

### 3. Release Documentation

`docs/releases/bilgeapi_v1.1.0_changelog.md` olusturulacak.

Kapsam:

- Faz 14-29 arasi eklenen ozellikler
- security guarantees
- verification evidence
- known exclusions / unrelated dirty files

### 4. Evidence Bundle

`docs/releases/bilgeapi_v1.1.0/` klasoru olusturulacak.

Kaydedilecek dosyalar:

- `backend_regression.txt`
- `migration_audit.txt`
- `release_gate.txt`
- `docker_build.txt`
- `docker_smoke.txt`
- `frontend_build.txt`
- `frontend_smoke.txt`
- `git_status_release.txt`
- `openapi_freeze_check.txt`
- `release_summary.md`
- `checksum_manifest.sha256`

### 5. Verification

Calistirilacak kontroller:

```powershell
py -3.13 scripts/export_bilgeapi_openapi.py
py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=term-missing
py -3.13 scripts/verify_bilgeapi_migrations.py
docker compose exec worker alembic current
py -3.13 scripts/run_release_gate.py
docker compose build bilgeapi
docker compose up -d bilgeapi
py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001
cmd /c npm.cmd run build
```

Frontend build `apps/refine_control_plane` altinda calistirilir.

### 6. Final Commit & Tag

Sadece Faz 30 release dosyalari stage edilecek:

- `implementation_plan.md`
- `task.md`
- `walkthrough.md`
- `docs/openapi/bilgeapi_openapi.v1.1.0.json`
- `docs/releases/bilgeapi_v1.1.0_workspace_audit.md`
- `docs/releases/bilgeapi_v1.1.0_changelog.md`
- `docs/releases/bilgeapi_v1.1.0/**`

Commit:

```powershell
git commit -m "chore: seal BilgeAPI v1.1.0 release"
```

Annotated tag:

```powershell
git tag -a bilgeapi-v1.1.0 -m "BilgeAPI v1.1.0 final release"
```

## Done Criteria

- [x] Baseline commit `2069a368` confirmed.
- [x] OpenAPI v1.1.0 freeze exists and validates.
- [x] Release evidence bundle exists.
- [x] Changelog exists.
- [x] Workspace audit exists.
- [x] Regression, migration, release gate, Docker smoke and frontend evidence are recorded.
- [x] Checksum manifest generated.
- [x] Final release commit created with only Faz 30 release files.
- [x] Annotated tag `bilgeapi-v1.1.0` points to final release commit.
