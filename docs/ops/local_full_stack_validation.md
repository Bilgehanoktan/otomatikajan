# Local and Full-Stack Validation

Bu doküman Faz 1 için local, minimal Docker ve full-stack Docker doğrulama adımlarını tanımlar.

## Amaç

Sistemin geliştirici makinesinde ve Docker tabanlı local stack üzerinde kontrollü şekilde çalıştığını kanıtlamak.

## Ön Koşullar

- Python 3.12+
- Docker ve Docker Compose
- Node.js 22+
- Git
- PowerShell veya Bash

## 1. Repo Hazırlığı

```bash
git clone https://github.com/Bilgehanoktan/otomatikajan.git
cd otomatikajan
git checkout codex/project-factory-policy-governance
cp .env.example .env
make secret
```

## 2. Local Dev Doğrulama

```bash
make install
make dev
```

Ayrı terminalde:

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8000/docs
```

Beklenen sonuç:

- API 8000 portunda açılır.
- `/health` 2xx döner.
- `/docs` 2xx döner.

## 3. Minimal Docker Doğrulama

```bash
docker compose up --build
```

Ayrı terminalde:

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8000/docs
```

Beklenen sonuç:

- `app` servisi healthy olur.
- `cms` servisi 3100 portunda erişilebilir olur.

## 4. Full-Stack Docker Doğrulama

```bash
docker compose --profile full-stack up --build
```

Beklenen servisler:

| Servis | Beklenen Durum |
|---|---|
| app | running / healthy |
| cms | running |
| db | healthy |
| redis | healthy |
| worker | running |
| deerflow-worker | running / healthy |
| beat | running |
| deerflow-bridge | running / healthy |
| bilgeapi | running / healthy |

Kontrol:

```bash
docker compose --profile full-stack ps
docker compose --profile full-stack logs --tail=100 app worker beat bilgeapi
curl -f http://localhost:8000/health
curl -f http://localhost:8100/health
```

## 5. PowerShell Smoke Test

Local dev:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1
```

Full-stack:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1 -Mode full-stack-local
```

Sadece erişim doğrulaması:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1 -SkipWorkflowDispatch
```

## 6. BilgeAPI Smoke

```bash
make bilgeapi-smoke
python scripts/smoke_bilgeapi.py --base-url http://localhost:8100 --api-key dev-test-key-001
```

## 7. Evidence Kaydı

Doğrulama sonrası `docs/evidence/` altında kayıt tutulmalıdır.

Önerilen dosya:

```text
YYYY-MM-DD_phase1_local_full_stack_checklist.md
```

Minimum sonuçlar:

- Local dev: Passed / Failed / Not run
- Minimal Docker: Passed / Failed / Not run
- Full-stack Docker: Passed / Failed / Not run
- BilgeAPI smoke: Passed / Failed / Not run
- Notes
