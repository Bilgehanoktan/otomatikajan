# Walkthrough — Faz 32B: External Agent Capability Registry & Sandbox

## Özet

Faz 32B, dış ajanların ana sisteme kontrolsüz erişmesini engelleyen capability registry, policy engine, sandbox executor ve redacted ledger hattını tamamlar.

Çalışma akışı:

```text
Agent request
-> Capability registry
-> Policy engine
-> Sandbox executor
-> Redacted run ledger
-> AgentRunModel audit trail
```

Bu fazdaki kritik güvenlik kararı: dış ajanlar serbest komut çalıştırmaz ve ana repo üzerinde doğrudan kontrolsüz işlem yapmaz.

## Doğrulanan Bileşenler

### Database Models

`libs/db/models/repair_models.py` içinde şu modeller vardır:

- `AgentCapabilityModel`
- `AgentRunModel`

### Migration

Faz 32B kapanış kontrolünde eksik olan Alembic migration tamamlandı:

```text
libs/db/migrations/alembic/versions/32b9c1d4e5f6_add_repair_agent_capability_tables.py
```

Bu migration şu tabloları oluşturur:

- `repair_agent_capabilities`
- `repair_agent_runs`

Migration table-existence check içerir ve JSON alanlarını SQLite/Postgres uyumlu tanımlar.

### Services

Faz 32B servisleri:

- `services/repair/external_agents/agent_capability_registry.py`
- `services/repair/external_agents/agent_policy_engine.py`
- `services/repair/external_agents/agent_sandbox_executor.py`
- `services/repair/external_agents/agent_ledger_reporter.py`

### Router

`services/repair/external_agents/router.py` external agent capability ve run endpointlerini sağlar.

`services/workflow_api/main.py` içinde router kaydı bulunur ve default capability registry startup sırasında initialize edilir.

## Güvenlik Özeti

Kapatılan riskler:

- Serbest shell execution engellenir.
- Ajanın repo dışına kaçması canonical path validation ile engellenir.
- Network policy default olarak kapalıdır.
- Agent output `stdout` / `stderr` redaction ve truncation sürecinden geçer.
- Agent run kayıtları `AgentRunModel` ve ledger reporter ile izlenebilir hale gelir.

## Kapanış Kontrolleri

Faz 32B kapanışı için çalıştırılması gereken doğrulamalar:

```powershell
py -3.13 -m pytest tests/repair/test_agent_registry_sandbox_phase32b.py -v
py -3.13 -c "import services.workflow_api.main; print('workflow api import ok')"
py -3.13 scripts/verify_bilgeapi_migrations.py
git show --name-only --stat HEAD
git tag --points-at HEAD
```

Çalıştırılan doğrulamalar:

```text
py -3.13 -m pytest tests/repair/test_agent_registry_sandbox_phase32b.py -v
Result: 6 passed

py -3.13 -c "import services.workflow_api.main; print('workflow api import ok')"
Result: workflow api import ok

py -3.13 scripts/verify_bilgeapi_migrations.py
Single head: yes
Current matches head: yes
Overall: PASS
Head/current: 32b9c1d4e5f6
```

Önceki test timeout nedeni sandbox’ın tüm repo kopyasını almasıydı. `AgentSandboxExecutor` artık minimal sandbox copy kullanır:

- `run_tests` için sadece gerekli top-level kaynaklar kopyalanır.
- `inspect_repo` için hedef dosya/dizin kopyalanır.
- `generate_patch` ve `browser_check` için gereksiz runtime/cache/artifact ağacı taşınmaz.

Bu değişiklik Faz 32B’nin güvenlik sınırını değiştirmez; ana repo hâlâ doğrudan mutate edilmez.

## Sonraki Faz Önerisi

Faz 32C için doğru yön:

```text
Agent Output Verification & Promotion Gate
```

32B ajanı güvenli sandbox içinde çalıştırır. 32C ise ajan çıktısının hash, artifact manifest, patch diff verification, VerifierMesh routing, human gate ve ledger proof üzerinden promote edilip edilemeyeceğini denetlemelidir.
