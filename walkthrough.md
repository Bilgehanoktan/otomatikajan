# Walkthrough - BilgeAPI Faz 28: Immutable Review Ledger + Evidence Chain Sealing

## Ozet

Faz 28 kapsaminda BilgeAPI self-improvement ve review workflow zincirine append-only, hash-chain tabanli `Immutable Review Ledger` eklendi. Ledger kayitlari payload'lari recursive redaction'dan gecirir, canonical JSON uzerinden SHA-256 hash hesaplar ve zincir butunlugunu `previous_hash` + `event_hash` ile dogrular.

## Yapilan Degisiklikler

### 1. Database & Migration
- `apps/bilgeapi/models/database.py` dosyasina `ReviewLedgerEntryModel` eklendi.
- Yeni tablo: `bilgeapi_review_ledger_entries`.
- Unique constraint: `chain_id + sequence_no`.
- Migration: `libs/db/migrations/alembic/versions/f28a0b1c2d3e_add_review_ledger_entries.py`.

### 2. Services
- `apps/bilgeapi/services/review_ledger.py` eklendi:
  - `PayloadRedactor`
  - `CanonicalPayloadHasher`
  - `ReviewLedgerService`
  - `ReviewLedgerVerifier`
- Redacted alanlar:
  - `plaintext_key`
  - `api_key`
  - `token`
  - `secret`
  - `authorization`
  - `github_token`
  - `webhook_secret`
  - `password`
  - `raw_content`

### 3. Repository & Schemas
- `ReviewLedgerRepository` arayuzu eklendi.
- `InMemoryReviewLedgerRepository` ve `PostgresReviewLedgerRepository` implementasyonlari eklendi.
- `apps/bilgeapi/schemas/review_ledger.py` ile chain, verify, append ve export response contract'lari tanimlandi.

### 4. API Endpoints
Yeni router: `apps/bilgeapi/routers/review_ledger.py`.

Eklenen endpoint'ler:
- `GET /v1/review-ledger/recent`
- `GET /v1/review-ledger/chains/{chain_id}`
- `GET /v1/review-ledger/chains/{chain_id}/verify`
- `GET /v1/review-ledger/chains/{chain_id}/export`
- `POST /v1/review-ledger/events`

RBAC:
- Recent/chain/verify: `bilgeapi.operator`
- Export/manual append: `bilgeapi.admin`

### 5. Lifecycle Integration
Ledger event yazimi su akislara eklendi:
- Research completion/failure
- Proposal creation
- Draft PR creation/failure
- Sandbox PR verification
- Reviewer feedback add/update
- Patch revision creation
- Patch revision verification

Ledger append islemleri best-effort calisir; ledger yazimi basarisiz olsa bile ana workflow kirilmaz.

### 6. Ops Console
`apps/refine_control_plane/src/lib/bilgeapiOpsClient.ts` ve `/bilgeapi-ops` sayfasi genisletildi:
- `listReviewLedgerRecent`
- `getReviewLedgerChain`
- `verifyReviewLedgerChain`
- `exportReviewLedgerChain`
- `Immutable Review Ledger` tab'i
- Chain load, verify, export ve payload preview

## Dogrulama

Calistirilan hedef testler:

```powershell
py -3.13 -m pytest tests/unit/bilgeapi/test_review_ledger.py tests/unit/bilgeapi/test_phase27_ops_console_static.py -q --tb=short --color=no
```

Sonuc:
- `6 passed`

Calistirilan BilgeAPI regresyon:

```powershell
py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing -q --tb=short --color=no
```

Sonuc:
- `201 passed`
- Coverage: `83.26%`

OpenAPI export:

```powershell
py -3.13 scripts/export_bilgeapi_openapi.py
```

Sonuc:
- `docs/openapi/bilgeapi_openapi.json` basariyla guncellendi.

Frontend build:

```powershell
cmd /c npm.cmd run build
```

Sonuc:
- Next.js production build basarili.

Docker build:

```powershell
docker compose build bilgeapi
```

Sonuc:
- Image basariyla build edildi.

Docker recreate ve migration:

```powershell
docker compose up -d bilgeapi
docker compose logs --tail=120 bilgeapi
```

Sonuc:
- Container `healthy`.
- Migration logu: `Running upgrade e1a49df5d6bb -> f28a0b1c2d3e, add_review_ledger_entries`.
- Alembic current: `f28a0b1c2d3e (head)`.

Release gate:

```powershell
docker compose exec -e BILGEAPI_STATIC_KEYS= -e BILGEAPI_STATIC_KEY_HASHES=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef:admin bilgeapi python scripts/run_release_gate.py
```

Sonuc:
- Score: `100.00`
- Status: `PASSED`
- Warnings: `0`
- Blockers: `0`
- Decision: `GO (PASSED)`

Live smoke:

```powershell
$env:PYTHONUTF8='1'; py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001
```

Sonuc:
- `6/6 passed - ALL PASSED`

Ledger endpoint smoke:

```powershell
GET http://127.0.0.1:8100/v1/review-ledger/recent
```

Sonuc:
- `HTTP 200`

Frontend route smoke:

```powershell
GET http://127.0.0.1:3100/bilgeapi-ops
```

Sonuc:
- `HTTP 200`
