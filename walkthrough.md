# Walkthrough — Unified Faz 31/32 Autonomous Governance

## Özet

Bu çalışma Faz 31 ve Faz 32 hattını tek bir güvenli otonom yönetim akışı olarak doğruladı ve eksik bağlantı noktalarını kapattı.

Birleşik akış:

```text
Signals -> Watchdog -> Findings -> Ledger -> Policy -> Controlled Remediation -> Evidence -> Operator Review
```

Sistem artık şu yetenekleri aynı runtime yüzeyinde birleştiriyor:

- Watchdog scan ve risk scoring.
- Deterministik finding dedupe ve lifecycle.
- Immutable ledger/audit kanıtı.
- Policy kontrollü remediation runbook/attempt kayıtları.
- Forbidden action ve human gate sınırları.
- Emergency recovery için yalnızca liveness recovery allowlist.
- UI repair / external recovery raporlarının governor hattına aktarımı.

## Güvenlik Sınırları

Otonom yönetim hattı bilinçli olarak aşağıdaki işlemleri yapmaz:

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

`SelfHealingExecutor` shell komutu çalıştırmaz; sadece kod içinde tanımlı kontrollü action handlerları simüle/çalıştırır.

## Uygulanan Birleştirme

### Router Bağlantısı

`apps/bilgeapi/main.py` içinde hem `system_watchdog` hem de `self_healing` routerları kayıtlıdır.

### Release Gate Bağlantısı

`apps/bilgeapi/services/release.py` içinde watchdog ve self-healing modül/endpoint kontrolleri release gate kapsamındadır.

Doğrulanan endpoint aileleri:

- `/v1/watchdog/run`
- `/v1/watchdog/status`
- `/v1/watchdog/findings`
- `/v1/watchdog/remediations`
- `/v1/watchdog/runbooks`
- `/v1/watchdog/emergency-recovery/run`
- `/v1/watchdog/findings/intake`
- `/v1/watchdog/external-recovery/report`

### Migration Durumu

Local SQLite fallback DB, Alembic head revizyonuna yükseltildi:

```text
007f130e456e (head)
```

`scripts/verify_bilgeapi_migrations.py` sonucu:

```text
Single head: yes
Current matches head: yes
Overall: PASS
```

## Test Sonuçları

### Hedef Testler

```powershell
py -3.13 -m pytest tests/unit/bilgeapi/test_system_watchdog.py tests/unit/bilgeapi/test_self_healing.py -v
```

Sonuç:

```text
20 passed
```

### Full BilgeAPI Regression

```powershell
py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing
```

Sonuç:

```text
235 passed
Total coverage: 82.57%
```

## Release Gate

```powershell
py -3.13 scripts/run_release_gate.py
```

Sonuç:

```text
Score: 100.00
Status: PASSED
Warnings: 0
Blockers: 0
Release Decision: GO (PASSED)
```

## OpenAPI

```powershell
py -3.13 scripts/export_bilgeapi_openapi.py
```

Sonuç:

```text
Successfully exported OpenAPI schema to: E:\ai_company_faz12.1\docs\openapi\bilgeapi_openapi.json
```

OpenAPI içinde `/v1/watchdog/*` endpointleri doğrulandı.

## Docker ve Smoke

Docker build:

```powershell
docker compose build --progress=plain bilgeapi
```

Sonuç:

```text
Image ai_company_faz121-bilgeapi Built
```

Container restart:

```powershell
docker compose up -d bilgeapi
```

Health:

```text
Up (healthy)
```

Smoke:

```powershell
$env:PYTHONUTF8='1'; py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001
```

Sonuç:

```text
Result: 6/6 passed - ALL PASSED
```

## Çalışma Alanı Notu

Workspace içinde bu fazdan bağımsız çok sayıda önceden kalmış dirty/generated dosya vardır. Commit sırasında yalnızca bu birleşik doğrulama ve router bağlantısı için ilgili dosyalar stage edilmelidir.
