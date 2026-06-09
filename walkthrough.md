# Walkthrough - BilgeAPI Faz 29: AI-Assisted Patch Revision Suggestions

Bu dokuman, Faz 29 kapsaminda eklenen AI destekli patch suggestion akisini, emniyet sinirlarini ve dogrulama kanitlarini ozetler.

## Ozet

Faz 29 ile BilgeAPI, reviewer feedback, mevcut patch revision, sandbox verification ve Faz 28 immutable review ledger baglamini kullanarak AI patch suggestion uretebilir hale geldi.

Temel guvenlik cizgisi korunur:

```text
AI onerir.
Sandbox dogrular.
Ledger muhurlenir.
Insan karar verir.
Sistem otomatik uygulamaz.
```

## Yapilan Degisiklikler

### 1. Configuration

`apps/bilgeapi/config.py` icine su guardrail ayarlari eklendi:

- `BILGEAPI_AI_PATCH_PROVIDER`
- `BILGEAPI_ALLOW_REAL_AI_PATCH`
- `BILGEAPI_AI_PATCH_MODEL`
- `BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS`
- `BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS`

Default provider `mock`, real provider flag default `false`.

### 2. Database & Migration

`apps/bilgeapi/models/database.py`:

- `AIPatchSuggestionModel`
- `PrVerificationModel.ai_suggestion_id`

Migration:

- `libs/db/migrations/alembic/versions/a29c4f83b2d1_add_ai_patch_suggestions.py`
- Container current head: `a29c4f83b2d1 (head)`

### 3. Provider, Service, Repository

Yeni dosyalar:

- `apps/bilgeapi/adapters/ai_patch_provider.py`
- `apps/bilgeapi/services/ai_patch_suggestion.py`
- `apps/bilgeapi/schemas/ai_patch_suggestion.py`

Repository katmani:

- `AIPatchSuggestionRepository`
- `InMemoryAIPatchSuggestionRepository`
- `PostgresAIPatchSuggestionRepository`

Servis akisi:

- Redacted context olusturur.
- Deterministik `prompt_hash` hesaplar.
- Output size limitini enforce eder.
- `SandboxPatchAnalyzer` ile risk analizi yapar.
- Suggestion'i DB'ye `GENERATED` olarak kaydeder.
- Verification sonrasi status'u `VERIFIED`, `NEEDS_REVISION` veya `BLOCKED` yapar.
- Accept/reject kararlari ledger'a yazilir.

### 4. Verification Integration

`PrVerificationService.verify_ai_suggestion` eklendi.

AI suggestion patch kodu mevcut Faz 25 scorer ile dogrulanir. HIGH risk suggestion score yuksek olsa bile `REVIEW_READY` olamaz; en fazla `NEEDS_HUMAN_CAUTION` olur.

### 5. API Endpoints

`apps/bilgeapi/routers/improvements.py` icine endpointler eklendi:

- `POST /v1/improvements/pr-drafts/{pr_draft_id}/ai-suggestions`
- `GET /v1/improvements/pr-drafts/{pr_draft_id}/ai-suggestions`
- `GET /v1/improvements/ai-suggestions/{suggestion_id}`
- `POST /v1/improvements/ai-suggestions/{suggestion_id}/verify`
- `POST /v1/improvements/ai-suggestions/{suggestion_id}/accept-for-review`
- `POST /v1/improvements/ai-suggestions/{suggestion_id}/reject`

RBAC:

- Generate/verify/accept/reject: `bilgeapi.admin`
- List/read: `bilgeapi.operator`

### 6. Ops Console

`apps/refine_control_plane` icinde:

- AI suggestion client methodlari eklendi.
- `/bilgeapi-ops` icine `AI Patch Suggestions` paneli eklendi.
- Generate, load, verify, accept, reject ve patch preview akislari eklendi.

## Dogrulama Sonuclari

### Target Tests

```powershell
py -3.13 -m pytest tests/unit/bilgeapi/test_ai_patch_suggestion.py tests/unit/bilgeapi/test_phase27_ops_console_static.py -q --tb=short --color=no
```

Sonuc:

```text
7 passed
```

### Full Regression + Coverage

```powershell
py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing -q --tb=short --color=no
```

Sonuc:

```text
206 passed
Total coverage: 82.46%
```

### OpenAPI

```powershell
py -3.13 scripts/export_bilgeapi_openapi.py
```

Sonuc:

```text
Successfully exported OpenAPI schema to docs/openapi/bilgeapi_openapi.json
```

### Frontend Build

```powershell
cmd /c npm.cmd run build
```

Sonuc:

```text
Compiled successfully
Route included: /bilgeapi-ops
```

### Frontend Route

```text
GET http://127.0.0.1:3100/bilgeapi-ops -> HTTP 200
```

### Docker & Smoke

```powershell
docker compose build bilgeapi
docker compose up -d bilgeapi
py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001
```

Sonuc:

```text
bilgeapi container: healthy
Smoke: 6/6 passed - ALL PASSED
OpenAPI AI suggestion path: present
```

### Release Gate

Local ve container release gate sonuclari:

```text
Score: 100.00
Status: PASSED
Warnings: 0
Blockers: 0
Release Decision: GO (PASSED)
```

## Sonuc

Faz 29 uygulanmis, test edilmis ve runtime/container ortaminda dogrulanmistir. AI patch suggestion akisi sadece insan review'una taslak uretir; otomatik apply, branch, commit, merge, deploy veya migration apply yapmaz.
