# Implementation Plan — BilgeAPI Unified Autonomous Governance

## Amaç

Bu plan Faz 31 ve Faz 32 hattını tek bir güvenli işletim mimarisinde birleştirir:

```text
Signals -> Watchdog -> Findings -> Ledger -> Policy -> Controlled Remediation -> Evidence -> Operator Review
```

Sistem kendi kendini izler, risk puanlar, finding üretir, remediation önerir ve izinli read-only / kontrollü aksiyonları policy üzerinden çalıştırır. Kritik sınır korunur: sistem `merge`, `deploy`, `branch push`, `production migration apply`, `API key revoke`, `secret rotation`, `force push` veya production config değişikliği yapmaz.

## Birleşen Fazlar

### Faz 31A — Acting Governor / Watchdog Core

- `SystemFindingModel` ile sistem bulguları kalıcı hale gelir.
- `SystemWatchdogService`, `SystemSignalCollector`, `SystemRiskScorer`, `SystemFindingService`, `WatchdogEvidenceBuilder` ve `ActingGovernorPolicy` çalışır.
- Finding dedupe deterministik `source_hash` ile yapılır.
- Terminal statüler (`DISMISSED`, `RESOLVED`) implicit reopen yapmaz.
- Endpointler:
  - `POST /v1/watchdog/run`
  - `GET /v1/watchdog/status`
  - `GET /v1/watchdog/findings`
  - `GET /v1/watchdog/findings/{finding_id}`
  - `POST /v1/watchdog/findings/{finding_id}/acknowledge`
  - `POST /v1/watchdog/findings/{finding_id}/dismiss`

### Faz 31B+ — Controlled Self-Healing

- `RemediationRunbookModel` ve `RemediationAttemptModel` ile runbook ve attempt kayıtları tutulur.
- `SelfHealingPolicy` forbidden action listesini enforce eder:
  - `auto_merge`
  - `auto_deploy`
  - `auto_revoke_key`
  - `production_migration_apply`
  - `migration_downgrade`
  - `branch_push`
  - `production_config_change`
  - `database_delete`
  - `secret_rotation`
  - `force_push`
- `SelfHealingExecutor` sadece allowlisted handler çalıştırır; shell komutu çalıştırmaz.
- `EmergencyRecoveryService` yalnızca `CRITICAL` severity ve liveness recovery action için çalışır.
- Endpointler:
  - `GET /v1/watchdog/remediations`
  - `GET /v1/watchdog/remediations/{attempt_id}`
  - `POST /v1/watchdog/findings/{finding_id}/remediate`
  - `GET /v1/watchdog/runbooks`
  - `POST /v1/watchdog/runbooks/{runbook_id}/enable`
  - `POST /v1/watchdog/runbooks/{runbook_id}/disable`
  - `POST /v1/watchdog/emergency-recovery/run`
  - `POST /v1/watchdog/findings/intake`
  - `POST /v1/watchdog/external-recovery/report`

### Faz 32 — UI Repair Governance Bridge

- UI repair ve external agent patch akışları governor policy hattına bağlanır.
- `AuditGate`, `VerifierMesh`, review gate, patch identity hash ve evidence hash kontrolleri korunur.
- UI onarım tarafında HTTP `200` tek başına yeterli kabul edilmez; browser/page audit ve console/page error kontrolleri gerekir.

## Güvenlik Kararları

- `BILGEAPI_SELF_HEALING_ENABLED=false` varsayılanda self-healing no-op / blocked davranır.
- `BILGEAPI_SELF_HEALING_SAFE_MODE=true` varsayılanda sadece `BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS` içindeki actionlar değerlendirilebilir.
- `BILGEAPI_EMERGENCY_RECOVERY_ENABLED=false` varsayılanda emergency recovery kapalıdır.
- `HIGH` severity finding için human gate gerekir.
- `CRITICAL` severity finding için sadece liveness recovery actionları emergency modda değerlendirilebilir.
- Ledger payloadlarında secret, token ve API key sızıntısı yapılmaz.

## Uygulama Adımları

1. Watchdog ve self-healing routerlarının `apps/bilgeapi/main.py` içine kayıtlı olduğunu doğrula.
2. Release gate `REQUIRED_MODULES` ve `REQUIRED_ENDPOINTS` listelerinde watchdog/self-healing modüllerini ve endpointlerini doğrula.
3. Migration zincirinde `SystemFindingModel`, `RemediationRunbookModel` ve `RemediationAttemptModel` tablolarını doğrula.
4. Unit/integration testleri çalıştır ve coverage >= 80% olduğunu doğrula.
5. OpenAPI şemasını export et.
6. Release gate scorecard çalıştır.
7. Docker build/up ve smoke test ile runtime davranışı doğrula.
8. Sadece bu birleşik fazla ilgili plan, walkthrough ve gerekiyorsa kod dosyalarını stage/commit et.

## Doğrulama Planı

```powershell
py -3.13 -m pytest tests/unit/bilgeapi/test_system_watchdog.py tests/unit/bilgeapi/test_self_healing.py -v
py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing
py -3.13 scripts/export_bilgeapi_openapi.py
py -3.13 scripts/run_release_gate.py
docker compose build bilgeapi
docker compose up -d bilgeapi
$env:PYTHONUTF8='1'; py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001
```

## Kabul Kriterleri

- Watchdog + self-healing hedef testleri geçer.
- BilgeAPI unit/integration suite geçer.
- Coverage >= 80%.
- Release gate `Score: 100.00`, `Status: PASSED`, `Decision: GO`.
- `/v1/watchdog/*` endpointleri OpenAPI içinde görünür.
- Docker smoke `6/6 passed`.
- Kirli workspace içinde ilgisiz dosyalar release commitine dahil edilmez.
