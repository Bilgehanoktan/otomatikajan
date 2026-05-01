# PC'de Calistirma

Bu belge Faz 1 runtime modelini esas alir. Sistem artik uc resmi profille dusunulur:

- `local-dev`: minimal local topology, `inprocess` queue, Redis/DeerFlow kapali
- `full-stack-local`: Docker ile Redis + Celery + DeerFlow acik yerel stack
- `production`: static UI + primary DB + Redis/Celery scheduler

## Onerilen baslangic yolu

### 1. `.env` hazirla
```bash
cp .env.example .env
```

### 2. Minimum gerekli degerleri gir
```env
APP_ENV=development
RUNTIME_PROFILE=local-dev
QUEUE_BACKEND=inprocess
JWT_SECRET=<python -c "import secrets; print(secrets.token_hex(64))">
ADMIN_SECRET=gizli-admin-sifresi
OPENAI_API_KEY=sk-...
```

## Modlar

### Minimal local topology

Bu mod normal gelistirme icin varsayilan hedeftir.

- UI: `3100`
- API/WS: `8000`
- Queue: `inprocess`
- Redis: kapali
- DeerFlow: kapali
- Scheduler: kapali

Baslatma:
```bash
BASLAT.bat
```

veya Docker aciksa acik secimle:
```bash
BASLAT.bat minimal
```

Smoke:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1 -Mode local-dev
```

### Full-stack local topology

Bu mod entegrasyon calismalari icindir.

- UI: `3100`
- API/WS: `8000`
- Queue: `celery`
- Redis: acik
- Postgres: acik
- DeerFlow bridge/worker: acik
- Scheduler: varsayilan olarak kapali

Baslatma:
```bash
BASLAT.bat fullstack
```

Smoke:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1 -Mode full-stack-local
```

## Docker olmadan local Python

### Gereksinimler
- Python 3.12+
- PostgreSQL 15+ sadece `full-stack-local` benzeri bir akis hedefleniyorsa
- Redis sadece `celery` kullaniliyorsa

### Minimal local calisma
```bash
pip install -e ".[dev]"
cp .env.example .env
```

`.env` icinde:
```env
APP_ENV=development
RUNTIME_PROFILE=local-dev
QUEUE_BACKEND=inprocess
REDIS_ENABLED=false
DEERFLOW_ENABLED=false
```

Calistir:
```bash
make run
```

## Ozet komutlar

| Komut | Aciklama |
|-------|----------|
| `BASLAT.bat` | Varsayilan minimal local topology |
| `BASLAT.bat minimal` | Docker ile minimal local topology |
| `BASLAT.bat fullstack` | Docker ile full-stack local topology |
| `DURDUR.bat` | Docker ve local surecleri durdur |
| `make run` | Local Python gelistirme sunucusu |
| `make test` | Tum testleri calistir |

## Telegram Bot

Telegram bot halen opsiyoneldir. Faz 2'de tam entegrasyon hedeflenir. Simdilik:

1. `TELEGRAM_ENABLED=true` yapmadan once bot token ve izinli ID'leri girin
2. `TELEGRAM_BOT_TOKEN=...`
3. `TELEGRAM_ALLOWED_IDS=...`
