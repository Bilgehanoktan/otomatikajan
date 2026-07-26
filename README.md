# OtomatikAjan

> 8 AI ajan, çoklu LLM, kalite kontrol, self-healing, GitHub issue-to-PR otomasyonu ve insan onay kapısı ile kontrollü otonom yazılım geliştirme platformu.

[![CI](https://github.com/Bilgehanoktan/otomatikajan/actions/workflows/ci.yml/badge.svg?branch=codex/project-factory-policy-governance)](https://github.com/Bilgehanoktan/otomatikajan/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)

## Ana Repo ve Branch

```text
Repository: Bilgehanoktan/otomatikajan
Primary working branch: codex/project-factory-policy-governance
Target autonomy level: L4.5 — staging'e kadar otonom, production'da insan onaylı
```

Bu branch, OtomatikAjan sisteminin tam otonom dönüşüm çalışmaları için ana çalışma zemini olarak kabul edilir.

## Mimari

```text
POST /api/v1/tasks veya GitHub issue
     │
     ▼
Task intake / JobQueue
     │
     ▼
Orchestrator.run_project()
     │
     ├─► ContextBuilder ← Memory / pgvector / sqlite fallback
     │
     ├─► 8 × SubTask / Agent
     │      ├─► ModelOrchestrator
     │      ├─► AgentOutputParser
     │      ├─► QualityScorer
     │      └─► ReviewerAgent
     │
     ├─► SelfHealEngine
     │
     └─► EventBus → WebSocket → DB audit → Webhook
```

## Ajan Rolleri

| Ajan | Rol | Ana Sorumluluk |
|---|---|---|
| architect | Yazılım mimarı | Mimari kararlar, tasarım, sınırlar |
| backend_dev | Backend geliştirici | FastAPI, servisler, API akışları |
| frontend_dev | Frontend geliştirici | Control plane UI, React/Next.js |
| qa_engineer | QA mühendisi | Test, smoke, E2E, kabul kriterleri |
| devops | DevOps mühendisi | Docker, CI/CD, deployment |
| security | Güvenlik uzmanı | Auth, secret, OWASP, risk |
| data_eng | Veri mühendisi | DB, migration, pgvector, memory |
| tech_writer | Teknik yazar | README, runbook, ADR, docs |
| deerflow | DeerFlow bridge | Uzun ve karmaşık ajan akışları |

## Hızlı Başlangıç

```bash
git clone https://github.com/Bilgehanoktan/otomatikajan.git
cd otomatikajan
git checkout codex/project-factory-policy-governance
cp .env.example .env
make secret
make install
make dev
```

Doğrulama:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Docker ile Çalıştırma

Minimal local topology:

```bash
docker compose up --build
```

Full-stack local topology:

```bash
docker compose --profile full-stack up --build
```

Full-stack modda şu servisler beklenir:

| Servis | Port | Açıklama |
|---|---:|---|
| API | 8000 | FastAPI backend |
| UI | 3100 | Control plane frontend |
| Postgres/pgvector | 5433 | Local DB |
| Redis | 6380 | Celery / rate limit |
| DeerFlow bridge | 8010 | Uzun ajan akışları |
| BilgeAPI | 8100 | Incident & repair orchestration API |

## Smoke Test

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1
```

Full-stack için:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1 -Mode full-stack-local
```

Workflow dispatch adımı olmadan sadece erişim kontrolü:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1 -SkipWorkflowDispatch
```

## BilgeAPI

BilgeAPI, ana uygulamadan ayrı çalışan incident intake, diagnostic lifecycle ve repair request governance API'sidir. Varsayılan portu `8100`'dür.

```bash
make bilgeapi-dev
make bilgeapi-build
make bilgeapi-test
make bilgeapi-smoke
make bilgeapi-openapi
make bilgeapi-release
```

Docker full-stack:

```bash
docker compose --profile full-stack up bilgeapi db --build
```

Smoke:

```bash
python scripts/smoke_bilgeapi.py
python scripts/smoke_bilgeapi.py --base-url http://localhost:8100 --api-key dev-test-key-001
```

## Test ve Kalite Kapıları

```bash
make test
make test-cov
make lint
make security
make docker-build
```

GitHub Actions kalite kapıları:

- Ruff lint
- Ruff format check
- Bandit security scan
- pip-audit
- Backend pytest
- Backend import smoke
- Production import smoke
- UI E2E Playwright
- Frontend lint/build
- Docker build gate

## Otonomi ve Governance

Bu proje için hedef kontrolsüz tam otonomi değildir. Hedef:

```text
L4.5 — staging'e kadar otonom, production'da insan onaylı.
```

Temel kural:

- Ajan issue açabilir.
- Ajan branch ve PR hazırlayabilir.
- Ajan test/smoke/evidence üretebilir.
- Ajan staging'e kadar kontrollü akış tetikleyebilir.
- Production deploy, rollback, secret değişimi, migration ve PR merge insan onayı olmadan yapılamaz.

İlgili dokümanlar:

- `docs/ops/autonomous_phase_plan.md`
- `docs/ops/governance_policy.md`
- `docs/architecture/agent_output_contract.md`
- `docs/ops/deployment_runbook.md`
- `docs/ops/rollback_playbook.md`
- `docs/ops/incident_response.md`
- `docs/evidence/README.md`

## Agent Output Contract

Her ajan çıktısı şu temel alanları taşımalıdır:

```json
{
  "agent": "backend_dev",
  "task_id": "issue-123",
  "summary": "Değişiklik özeti",
  "intent": "code_change",
  "risk": "low",
  "needs_human_approval": false,
  "files_to_change": [],
  "proposed_changes": [],
  "tests": [],
  "rollback_plan": "Geri alma yaklaşımı",
  "evidence": [],
  "blocked_by": []
}
```

Detaylı sözleşme: `docs/architecture/agent_output_contract.md`

## Environment ve Secret Yönetimi

```bash
cp .env.example .env
make secret
```

Gerçek secret'lar repository içine yazılmaz. `.gitignore` içinde `.env`, `.env.local`, `.env.production`, `.env.*` ve lokal runtime dosyaları ignore edilir.

Otonomi modu için ana değişkenler:

```env
AUTONOMY_MODE=supervised
AUTONOMY_SAFE_MODE=false
AUTONOMY_REQUIRE_HUMAN_APPROVAL_FOR_PRODUCTION=true
AUTONOMY_ALLOW_PRODUCTION_DEPLOY=false
AUTONOMY_ALLOW_SECRET_MUTATION=false
AUTONOMY_ALLOW_DB_MIGRATION=false
```

Kill-switch için:

```env
AUTONOMY_MODE=read_only
```

## Release ve Deployment

Release tag standardı:

```text
otomatikajan-vX.Y.Z
```

Release check:

```text
GitHub Actions → Release Check — Controlled Deployment
```

Production için minimum şartlar:

- CI başarılı.
- Security scan kabul edilebilir.
- Docker build başarılı.
- Staging smoke test başarılı.
- Rollback planı mevcut.
- Evidence kaydı mevcut.
- İnsan onayı verilmiş.

## Operasyonel Dokümanlar

| Doküman | Amaç |
|---|---|
| `docs/ops/autonomous_phase_plan.md` | Faz planı |
| `docs/ops/project_identity.md` | Proje kimliği |
| `docs/ops/branch_strategy.md` | Branch ve release stratejisi |
| `docs/ops/secret_handling.md` | Secret yönetimi |
| `docs/ops/local_full_stack_validation.md` | Local/full-stack doğrulama |
| `docs/ops/governance_policy.md` | Yetki ve risk sınırları |
| `docs/ops/deployment_runbook.md` | Deployment akışı |
| `docs/ops/rollback_playbook.md` | Rollback akışı |
| `docs/ops/incident_response.md` | Incident akışı |
| `docs/evidence/README.md` | Kanıt standardı |

## Geliştirici Komutları

```bash
make install
make dev
make test
make lint
make security
make docker-build
make docker-up
make docker-down
make migrate
make celery
make secret
```

## Güvenlik Notu

Production etkili her aksiyon için insan onayı şarttır. Bu proje için L5, yani tamamen onaysız production otonomisi, hedeflenmez.
