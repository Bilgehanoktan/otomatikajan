# Implementation Plan — Faz 32B: External Agent Capability Registry & Sandbox

## Amaç

Faz 32B, dış ajanların sisteme kontrolsüz erişmesini engelleyen capability registry, policy engine, sandbox executor ve ledger kayıt hattını tamamlar.

Hedef akış:

```text
Agent request -> Capability registry -> Policy engine -> Sandbox executor -> Redacted run ledger -> AgentRunModel audit trail
```

Bu faz dış ajanı doğrudan ana repo üzerinde serbest çalıştırmaz. Ajan isteği önce capability kaydı ve policy kurallarından geçer; ardından sadece izinli handler ve sandbox sınırları içinde yürütülür.

## Güvenlik Sınırları

- Default ajanlar disabled gelir.
- Default sandbox modu `read-only`.
- `requires_human_approval` default `true`.
- `shell=True` kullanılmaz.
- Komut çalıştırma handler allowlist mantığına bağlıdır.
- Canonical path validation repo dışına kaçışı engeller.
- Network policy default `disabled`.
- `stdout` / `stderr` redaction ve truncation uygulanır.
- Her run ledger/audit trail üzerinde izlenebilir.

## Kapsam

### Database Models

`libs/db/models/repair_models.py` içinde:

- `AgentCapabilityModel`
  - `repair_agent_capabilities`
  - `agent_key`, `agent_name`, `enabled`, `risk_level`
  - `allowed_directories`, `blocked_directories`
  - `allowed_commands`, `blocked_commands`
  - `sandbox_mode`, `network_policy`, `allowed_domains`
  - `requires_human_approval`

- `AgentRunModel`
  - `repair_agent_runs`
  - `run_id`, `agent_key`, `status`, `workspace_path`
  - `input_parameters`, `commands_executed`, `policy_violations`
  - `stdout`, `stderr`, `cost`, hash alanları, `ledger_chain_id`

### Migration

Yeni Alembic migration:

```text
libs/db/migrations/alembic/versions/32b9c1d4e5f6_add_repair_agent_capability_tables.py
```

Oluşturulan tablolar:

- `repair_agent_capabilities`
- `repair_agent_runs`

Migration idempotent table-existence check içerir ve JSON alanları SQLite/Postgres uyumlu tanımlar.

### Services

- `services/repair/external_agents/agent_capability_registry.py`
- `services/repair/external_agents/agent_policy_engine.py`
- `services/repair/external_agents/agent_sandbox_executor.py`
- `services/repair/external_agents/agent_ledger_reporter.py`

### API

`services/repair/external_agents/router.py`:

- `GET /capabilities`
- `GET /capabilities/{agent_key}`
- `POST /capabilities/{agent_key}/enable`
- `POST /capabilities/{agent_key}/disable`
- `POST /runs`
- `GET /runs`
- `GET /runs/{run_id}`

Router `services/workflow_api/main.py` üzerinden kayıtlıdır.

## Doğrulama Planı

```powershell
py -3.13 -m pytest tests/repair/test_agent_registry_sandbox_phase32b.py -v
py -3.13 -c "import services.workflow_api.main; print('workflow api import ok')"
$env:DATABASE_URL='sqlite+aiosqlite:///runtime/data/cortex_local_v2.db'; py -3.13 -c "import os, sys; os.environ['DATABASE_URL']='sqlite+aiosqlite:///runtime/data/cortex_local_v2.db'; from alembic.config import main; sys.argv=['alembic','upgrade','head']; main()"
py -3.13 scripts/verify_bilgeapi_migrations.py
```

## Kabul Kriterleri

- `AgentCapabilityModel` ve `AgentRunModel` için gerçek DB migration vardır.
- Faz 32B testleri geçer.
- External agent router import edilir.
- Tag son Faz 32B kapanış commit’i üzerinde durur.
- `implementation_plan.md`, `task.md`, `walkthrough.md` Faz 32B’ye özel içerik taşır.
