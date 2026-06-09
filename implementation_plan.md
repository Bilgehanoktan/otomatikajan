# Implementation Plan - BilgeAPI Faz 29: AI-Assisted Patch Revision Suggestions

Bu faz, Faz 24-28 arasinda kurulan self-improvement zincirini reviewer feedback'e gore AI destekli patch revision onerileri uretecek sekilde genisletir.

Temel ilke:

```text
AI onerir.
Sandbox dogrular.
Ledger muhurlenir.
Insan karar verir.
Sistem otomatik uygulamaz.
```

## Goal

BilgeAPI, `PrDraftModel`, `PrReviewFeedbackModel`, `PatchRevisionModel`, `PrVerificationModel` ve Faz 28 `ReviewLedgerService` zincirini kullanarak yeni bir `AIPatchSuggestionModel` kaydi olusturur. Bu kayit yalnizca patch suggestion taslagi saklar; dosya sistemine, git branch'e, commit'e, PR merge'e, deploy'a veya migration apply akisina dokunmaz.

## Safety Rules

- Default provider `mock` olmalidir.
- `BILGEAPI_ALLOW_REAL_AI_PATCH=True` degilse `openai` veya `local` provider calismaz.
- AI prompt/context icine plaintext API key, token, secret, authorization, password, webhook secret veya raw web content giremez.
- `suggested_patch_code` DB'de taslak olarak saklanir; uygulanmaz.
- Her suggestion `SandboxPatchAnalyzer` ve `PrReviewGateScorer` kurallarindan gecmelidir.
- HIGH risk suggestion score yuksek olsa bile `REVIEW_READY` olamaz; en fazla `NEEDS_HUMAN_CAUTION` olur.
- Tum kritik olaylar Faz 28 immutable review ledger'a redacted payload ile yazilir.

## Proposed Changes

### 1. Configuration

`apps/bilgeapi/config.py` icine su ayarlar eklenir:

```python
BILGEAPI_AI_PATCH_PROVIDER = "mock"  # mock | openai | local
BILGEAPI_ALLOW_REAL_AI_PATCH = False
BILGEAPI_AI_PATCH_MODEL = "gpt-4.1-mini"
BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS = 12000
BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS = 8000
```

### 2. Database & Migration

`apps/bilgeapi/models/database.py`:

- `AIPatchSuggestionModel`
- `PrVerificationModel.ai_suggestion_id`

Migration:

- `bilgeapi_ai_patch_suggestions` tablosu
- `bilgeapi_pr_verifications.ai_suggestion_id` nullable index
- JSON alanlari mevcut `SmartJSON` / SQLite-Postgres uyumlu yaklasimla tutulur.

Not: `PrVerificationModel.pr_draft_id` ve `proposal_id` nullable yapilmaz. AI suggestion verification kayitlari da ilgili PR draft ve proposal uzerinden olusturulur.

### 3. Schemas

Yeni dosya: `apps/bilgeapi/schemas/ai_patch_suggestion.py`

- `AIPatchSuggestionRequest`
- `AIPatchSuggestionResponse`
- `AIPatchSuggestionDecisionRequest`
- `AIPatchSuggestionDecisionResponse`

### 4. Repositories

`AIPatchSuggestionRepository` interface ve Postgres/InMemory implementasyonlari eklenir:

- `create_suggestion`
- `get_suggestion`
- `list_suggestions_by_pr_draft`
- `update_suggestion_status`
- `attach_verification`

`update_suggestion_status` sadece durum ve `updated_at` gunceller; genel `metadata` parametresi kullanilmaz.

### 5. AI Patch Provider Layer

Yeni dosya: `apps/bilgeapi/adapters/ai_patch_provider.py`

- `BaseAIPatchProvider`
- `MockAIPatchProvider`
- `OpenAIPatchProvider`
- `LocalAIPatchProvider`

Gercek provider'lar feature flag kapaliyken hata verir. Mock provider deterministic calisir ve testlerde default kullanilir.

### 6. Services

Yeni dosya: `apps/bilgeapi/services/ai_patch_suggestion.py`

- `PatchSuggestionContextBuilder`
- `AIPatchSuggestionService`

Akis:

1. `pr_draft_id`, `feedback_id`, `revision_id` dogrulanir.
2. Context builder redacted ve boyut limitli context uretir.
3. `prompt_hash` canonical redacted context + instruction uzerinden deterministik hesaplanir.
4. Provider patch suggestion uretir.
5. Output size siniri enforce edilir.
6. `SandboxPatchAnalyzer` ile on risk analizi yapilir.
7. Suggestion DB'ye `GENERATED` olarak kaydedilir.
8. Ledger'a `AI_PATCH_SUGGESTION_GENERATED` yazilir.
9. Verification istendiginde mevcut `PrVerificationService.verify_ai_suggestion` kullanilir.
10. Status `VERIFIED`, `NEEDS_REVISION` veya `BLOCKED` olarak guncellenir.

### 7. Verification Integration

`apps/bilgeapi/services/pr_verification.py`:

- `verify_ai_suggestion(self, suggestion_id: str, actor_id: str) -> dict`

Bu metod:

- suggestion patch kodunu analiz eder.
- mevcut scorer ile review decision hesaplar.
- `PrVerificationModel` kaydina `ai_suggestion_id` yazar.
- suggestion status/risk/verification baglantisini gunceller.
- ledger event yazar.

### 8. API Endpoints

`apps/bilgeapi/routers/improvements.py`:

```http
POST /v1/improvements/pr-drafts/{pr_draft_id}/ai-suggestions
GET  /v1/improvements/pr-drafts/{pr_draft_id}/ai-suggestions
GET  /v1/improvements/ai-suggestions/{suggestion_id}
POST /v1/improvements/ai-suggestions/{suggestion_id}/verify
POST /v1/improvements/ai-suggestions/{suggestion_id}/accept-for-review
POST /v1/improvements/ai-suggestions/{suggestion_id}/reject
```

RBAC:

- Generate: `bilgeapi.admin`
- List/read: `bilgeapi.operator`
- Verify: `bilgeapi.admin`
- Accept/reject: `bilgeapi.admin`

### 9. Ops Console

`apps/refine_control_plane`:

- Client methods for AI patch suggestions.
- `/bilgeapi-ops` icinde `AI Patch Suggestions` paneli.
- Generate, verify, accept, reject, patch preview ve risk display.

### 10. Release Gate

`apps/bilgeapi/services/release.py` yeni module/endpoint kontrollerine Faz 29 parcalari eklenir:

- `apps.bilgeapi.services.ai_patch_suggestion`
- `apps.bilgeapi.adapters.ai_patch_provider`
- `apps.bilgeapi.schemas.ai_patch_suggestion`
- `/v1/improvements/ai-suggestions/{suggestion_id}`

Release gate ayrica config defaultlarini kontrol eder:

- provider default `mock`
- real AI patch flag default disabled

## Verification Plan

Target tests:

```powershell
py -3.13 -m pytest tests/unit/bilgeapi/test_ai_patch_suggestion.py tests/unit/bilgeapi/test_phase27_ops_console_static.py -q
```

Regression:

```powershell
py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing -q
```

OpenAPI:

```powershell
py -3.13 scripts/export_bilgeapi_openapi.py
```

Frontend:

```powershell
cmd /c npm.cmd run build
```

Release gate:

```powershell
py -3.13 scripts/run_release_gate.py
```

## Definition of Done

- [x] DB model ve migration tamamlandi.
- [x] Mock provider default calisiyor.
- [x] Real provider flag kapaliyken calismiyor.
- [x] Context redaction zorunlu.
- [x] Suggestion DB'ye kaydediliyor.
- [x] Suggestion sandbox verification'dan geciyor.
- [x] Risk downgrade kuralı korunuyor.
- [x] Ledger eventleri yaziliyor.
- [x] Ops Console AI Suggestion paneli eklendi.
- [x] Endpoint RBAC testleri geciyor.
- [x] Full regression geciyor.
- [x] Coverage >= 80%.
- [x] OpenAPI export guncellendi.
- [x] Frontend build geciyor.
- [x] Release gate PASSED / GO.
