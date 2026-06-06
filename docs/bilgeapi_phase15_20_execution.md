# BilgeAPI Phase 15-20 Execution Notes

## Phase 15 - Live Runtime Sync

Komut:

```powershell
docker compose build bilgeapi
docker compose --profile full-stack up -d bilgeapi
py -3.13 scripts\bilgeapi_live_smoke.py --base-url http://127.0.0.1:8100
```

Evidence: `docs/evidence/bilgeapi_phase15_live_smoke.md`

Sonuc: `Overall: PASS`; `/health`, `/metrics`, `/docs`, `/openapi.json` ve auth korumali `/v1/catalog` canli ortamda dogrulandi.

## Phase 16 - Production Hardening Smoke

Komut:

```powershell
py -3.13 scripts\verify_bilgeapi_production_hardening.py
```

Evidence: `docs/evidence/bilgeapi_phase16_production_hardening.md`

Sonuc: `Overall: PASS`; production modunda plaintext static fallback reddedildi, hashed admin key kabul edildi, private `/metrics` admin disi erisime kapandi ve `X-Tenant-ID` spoofing yok sayildi.

## Phase 17 - API Key Admin Operations

Runbook: `docs/bilgeapi_api_key_admin_runbook.md`

CLI:

```powershell
py -3.13 scripts\bilgeapi_api_key_admin.py --admin-api-key <ADMIN_KEY> list
```

## Phase 18 - Migration Verification

Komut:

```powershell
py -3.13 scripts\verify_bilgeapi_migrations.py
```

Evidence: `docs/evidence/bilgeapi_phase18_migration_verification.md`

Sonuc: `Overall: PASS`; Alembic tek head `5d8a1c2b7e90`, current revision head ile ayni.

## Phase 19 - Tenant Foundation

Bu sprintte `tenant_id` API key lifecycle modeline eklendi:

- `ApiKeyModel.tenant_id`
- `ApiKeyCreate.tenant_id`
- `ApiKeyResponse.tenant_id`
- DB-backed auth identity `tenant_id`
- Usage metering identity tabanli tenant okuma

Sonraki sprintte incident/audit/repair kayitlari tenant-scoped hale getirilmelidir.

## Phase 20 - Operations Dashboard Starter

Grafana dashboard artifact:

```text
docs/monitoring/bilgeapi_grafana_dashboard.json
```

Panel kapsami:

- Release gate score
- HTTP request rate/status
- p95 latency
- Tenant request metering
- Redis fallback count
- Webhook delivery/dead-letter count
- Pending background tasks

## Final Verification

```powershell
py -3.13 -m pytest tests\unit\bilgeapi tests\integration\bilgeapi --cov=apps.bilgeapi --cov-report=term-missing --cov-report=xml -q --tb=short --color=no
py -3.13 scripts\run_release_gate.py
py -3.13 scripts\verify_bilgeapi_production_hardening.py
py -3.13 scripts\verify_bilgeapi_migrations.py
py -3.13 scripts\bilgeapi_live_smoke.py --base-url http://127.0.0.1:8100
```

Sonuclar:

- Unit + integration: `169 passed`
- Coverage: `82.84%`
- Release gate: `Score: 100.00`, `Status: PASSED`, `Release Decision: GO`
- Production hardening smoke: `PASS`
- Migration verification: `PASS`
- Live smoke: `PASS`
