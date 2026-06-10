# Implementation Plan — BilgeAPI (Faz 31A: Acting Governor / Watchdog Core)

## Goal

Faz 31A, BilgeAPI v1.1.0 sonrası sisteme read-only Acting Governor / Watchdog çekirdeği ekler. Bu katman sadece sistem sinyallerini toplar, risk puanlar, `SystemFinding` üretir, finding lifecycle durumlarını yönetir ve immutable review ledger üzerinde kanıt bırakır.

Bu fazda sistem kesinlikle aşağıdaki işlemleri yapmaz:

- `auto_merge`
- `auto_deploy`
- `auto_revoke_key`
- `production_migration_apply`
- `branch_push`
- `production_config_change`

## Scope

### Database

- `SystemFindingModel` eklendi.
- Deterministik `source_hash` dedupe anahtarı kullanılır.
- `DISMISSED` ve `RESOLVED` terminal durumdur; implicit reopen yapılmaz.

### Config

- `BILGEAPI_WATCHDOG_ENABLED`
- `BILGEAPI_WATCHDOG_RISK_THRESHOLD`
- `BILGEAPI_WATCHDOG_AUTO_FINDING`
- `BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED`

Faz 31A sadece manual run destekler: `POST /v1/watchdog/run`.

### Services

- `SystemSignalCollector`
- `SystemRiskScorer`
- `SystemFindingService`
- `WatchdogEvidenceBuilder`
- `ActingGovernorPolicy`
- `SystemWatchdogService`

### API

- `POST /v1/watchdog/run`
- `GET /v1/watchdog/status`
- `GET /v1/watchdog/findings`
- `GET /v1/watchdog/findings/{finding_id}`
- `POST /v1/watchdog/findings/{finding_id}/acknowledge`
- `POST /v1/watchdog/findings/{finding_id}/dismiss`

### Ledger Events

- `WATCHDOG_SCAN_STARTED`
- `WATCHDOG_SCAN_COMPLETED`
- `SYSTEM_FINDING_CREATED`
- `SYSTEM_FINDING_DEDUPED`
- `SYSTEM_FINDING_ACKNOWLEDGED`
- `SYSTEM_FINDING_DISMISSED`

## Verification Plan

1. `py -3.13 -m pytest tests/unit/bilgeapi/test_system_watchdog.py -v`
2. `py -3.13 -m pytest tests/unit/bilgeapi -q`
3. `py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing`
4. `py -3.13 scripts/export_bilgeapi_openapi.py`
5. `py -3.13 scripts/run_release_gate.py`
6. `docker compose build bilgeapi`
7. `docker compose up -d bilgeapi`
8. `py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001`
