# Walkthrough — BilgeAPI Faz 31A: Acting Governor / Watchdog Core

## Özet

Faz 31A kapsamında BilgeAPI'ye read-only Acting Governor / Watchdog çekirdeği eklendi. Sistem artık release gate, review ledger ve güvenli konfigürasyon sinyallerini manuel olarak tarayabiliyor, risk puanı hesaplıyor, dedupe edilen `SystemFinding` kayıtları üretiyor ve lifecycle işlemlerini immutable review ledger üzerinde kanıtlıyor.

Bu fazda otomatik merge, deploy, API key revoke, production migration apply, branch push veya production config değişikliği yoktur.

## Yapılan Değişiklikler

### 1. Config

`apps/bilgeapi/config.py` dosyasına watchdog ayarları eklendi:

- `BILGEAPI_WATCHDOG_ENABLED`
- `BILGEAPI_WATCHDOG_RISK_THRESHOLD`
- `BILGEAPI_WATCHDOG_AUTO_FINDING`
- `BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED`

Varsayılan çalışma modu güvenlidir: watchdog disabled ve yalnızca manual-run endpoint üzerinden çalışır.

### 2. Database & Repository

`apps/bilgeapi/models/database.py` dosyasına `SystemFindingModel` eklendi. Yeni tablo:

- `bilgeapi_system_findings`
- deterministic `source_hash`
- `occurrence_count`
- lifecycle timestamp alanları
- BilgeAPI research/proposal/PR/verification/ledger bağlantı alanları

Migration:

- `libs/db/migrations/alembic/versions/b31a0f1e2d3c_add_bilgeapi_system_findings.py`

Migration hem SQLite fallback hem local PostgreSQL geliştirme DB üzerinde uygulandı:

```powershell
py -3.13 -m alembic upgrade head
```

### 3. Watchdog Services

Yeni servis:

- `apps/bilgeapi/services/system_watchdog.py`

Eklenen sınıflar:

- `SystemSignalCollector`
- `SystemRiskScorer`
- `SystemFindingService`
- `WatchdogEvidenceBuilder`
- `ActingGovernorPolicy`
- `SystemWatchdogService`

Güvenlik sınırı:

- `ActingGovernorPolicy.FORBIDDEN_ACTIONS` içinde `auto_merge`, `auto_deploy`, `auto_revoke_key`, `production_migration_apply`, `branch_push`, `production_config_change` sabit olarak yasaklandı.
- Production ortamında `BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED=false` kabul edilmez.
- `DISMISSED` ve `RESOLVED` terminal statüdür; implicit reopen yapılmaz.

### 4. API Endpoints

Yeni router:

- `apps/bilgeapi/routers/system_watchdog.py`

Endpointler:

- `POST /v1/watchdog/run`
- `GET /v1/watchdog/status`
- `GET /v1/watchdog/findings`
- `GET /v1/watchdog/findings/{finding_id}`
- `POST /v1/watchdog/findings/{finding_id}/acknowledge`
- `POST /v1/watchdog/findings/{finding_id}/dismiss`

RBAC:

- `run`, `acknowledge`, `dismiss`: `bilgeapi.admin`
- `status`, `findings`, `finding detail`: `bilgeapi.operator`

### 5. Release Gate Integration

`apps/bilgeapi/services/release.py` içindeki required module ve endpoint listeleri watchdog modül ve endpointleriyle güncellendi.

Release gate sonucu:

```text
Score: 100.00
Status: PASSED
Warnings: 0
Blockers: 0
Decision: GO (PASSED)
```

## Doğrulama Sonuçları

### Faz 31A Unit Tests

```powershell
py -3.13 -m pytest tests/unit/bilgeapi/test_system_watchdog.py -v
```

Sonuç:

```text
9 passed
```

### BilgeAPI Unit Regression

```powershell
py -3.13 -m pytest tests/unit/bilgeapi -q
```

Sonuç:

```text
passed
```

### Unit + Integration + Coverage

```powershell
py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing
```

Sonuç:

```text
215 passed
Total coverage: 82.33%
```

### Docker & Smoke

```powershell
docker compose build bilgeapi
docker compose up -d bilgeapi
py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001
```

Sonuç:

```text
bilgeapi: healthy
Smoke: 6/6 passed - ALL PASSED
```

### Live Watchdog Endpoint Smoke

```text
GET /v1/watchdog/status -> HTTP 200
POST /v1/watchdog/run -> HTTP 200
```

Varsayılan disabled durumda safe no-op dönmektedir:

```json
{
  "status": "DISABLED",
  "enabled": false,
  "findings_created": 0,
  "forbidden_actions": [
    "auto_merge",
    "auto_deploy",
    "auto_revoke_key",
    "production_migration_apply",
    "branch_push",
    "production_config_change"
  ]
}
```
