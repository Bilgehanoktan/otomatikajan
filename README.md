# 🏢 Otonom Yazılım Geliştirme Şirketi

> **8 AI Ajan | Çoklu LLM (OpenAI + Claude + Gemini) | Öz-İyileştirme | Kalite Kontrol | İnsan Onayı Kapısı**

[![CI](https://github.com/your-org/ai-yazilim-sirketi/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/ai-yazilim-sirketi/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)

---

## 📋 İçindekiler

1. [Mimari](#mimari)
2. [Hızlı Başlangıç](#hızlı-başlangıç)
3. [Kurulum (Manuel)](#kurulum-manuel)
4. [Docker ile Başlatma](#docker-ile-başlatma)
5. [Ortam Değişkenleri](#ortam-değişkenleri)
6. [API Kullanımı](#api-kullanımı)
7. [Celery Görev Kuyruğu](#celery-görev-kuyruğu)
8. [Test](#test)
9. [Güvenlik](#güvenlik)
10. [Dağıtım (Üretim)](#dağıtım-üretim)

---

## Mimari

```
POST /projects
     │
     ▼
JobQueue (async)
     │
     ▼
Orchestrator.run_project()
     │
     ├─► ContextBuilder  ← Memory (pgvector / in-memory)
     │
     ├─► 8 × SubTask (paralel)
     │        │
     │        ├─► ModelOrchestrator (OpenAI → Claude → Gemini)
     │        ├─► AgentOutputParser  (JSON şema)
     │        ├─► QualityScorer      (5 boyut, 0.0–1.0)
     │        └─► ReviewerAgent      (skor < 0.60 ise revize)
     │
     ├─► SelfHealEngine (5sn döngü, FSM)
     │
     └─► EventBus → WS broadcast + DB audit + Webhook
```

### 8 Uzman Ajan

| Ajan | Rol | Uzmanlık |
|------|-----|----------|
| 🏛️ architect | Yazılım Mimarı | Sistem tasarımı, mimari desenler |
| ⚙️ backend_dev | Backend Geliştirici | Python, FastAPI, asyncio |
| 🎨 frontend_dev | Frontend Geliştirici | React, TypeScript, Next.js |
| 🧪 qa_engineer | QA Mühendisi | Test stratejisi, Playwright |
| 🚀 devops | DevOps Mühendisi | Docker, K8s, CI/CD |
| 🔒 security | Güvenlik Uzmanı | OWASP, pentest, güvenli kod |
| 🗄️ data_eng | Veri Mühendisi | PostgreSQL, Redis, pipeline |
| 📝 tech_writer | Teknik Yazar | API docs, ADR, README |
| 🦌 deerflow | DeerFlow Bridge | Ağır mantıksal akışlar, LangGraph entegrasyonu |

### 🦌 DeerFlow Köprüsü (Bridge)

Sistem, karmaşık ve uzun süreli ajan görevlerini yönetmek için **DeerFlow** harness'ını bir mikro-servis olarak kullanır:
- **Konum:** `deerflow-bridge` (Port 8010)
- **Kuyruk:** `deerflow_run` (Celery)
- **LLM:** Groq / Llama-3.3 (Düşük gecikme, yüksek kapasite)
- **Akış:** FastAPI üzerinden SSE (Server-Sent Events) ile worker'a gerçek zamanlı veri aktarımı.
- **Verifikasyon:** Faz 1 entegrasyonu `tests/test_deerflow_routing_contract.py` ve `tests/test_deerflow_task_contract.py` ile doğrulanmıştır.

---

## Hızlı Başlangıç

```bash
# Repoyu klonla
git clone https://github.com/your-org/ai-yazilim-sirketi.git
cd ai-yazilim-sirketi

# .env.local oluştur (Gerçek secret'lar repository içine commit edilmemelidir)
cp .env.example .env.local

# JWT_SECRET üret (OWASP min 64 karakter)
make secret
# Çıktıyı .env dosyasına JWT_SECRET=... olarak yapıştır

# Docker ile başlat
make docker-up

# API'yi test et
curl http://localhost:8000/health
# API docs: http://localhost:8000/docs
```

---

## Kurulum (Manuel)

**Gereksinimler:** Python 3.12+, PostgreSQL 15+ (pgvector), Redis 7+

```bash
# Sanal ortam
python -m venv .venv && source .venv/bin/activate

# Bağımlılıklar
make install

# .env hazırla
cp .env.example .env.local   # değerleri doldur (Repository'ye commit etmeyin!)

# Veritabanı migrasyonu
make migrate

# Geliştirme sunucusu
make dev
```

---

## Docker ile Başlatma

```bash
make docker-up      # PostgreSQL + Redis + App + Celery Worker
make docker-logs    # logları izle
make docker-down    # durdur
```

Servisler: **API** → http://localhost:8000 | **Docs** → http://localhost:8000/docs

---

## Ortam Değişkenleri

| Değişken | Zorunlu | Açıklama |
|----------|---------|----------|
| `OPENAI_API_KEY` | \* | OpenAI API anahtarı |
| `ANTHROPIC_API_KEY` | \* | Anthropic Claude API anahtarı |
| `GEMINI_API_KEY` | \* | Google Gemini API anahtarı |
| `DATABASE_URL` | Evet | `postgresql+asyncpg://...` |
| `REDIS_URL` | Hayır | Redis URL (Celery + dağıtık rate limit) |
| `JWT_SECRET` | Evet | **Min 64 karakter** — `make secret` ile üret |
| `ADMIN_SECRET` | Evet (prod) | Admin endpoint koruması |
| `ALLOWED_ORIGINS` | Hayır | Virgülle ayrılmış CORS origin'leri |
| `ENVIRONMENT` | Hayır | `development` / `production` |
| `LLM_TIMEOUT_S` | Hayır | LLM zaman aşımı saniyesi (varsayılan: 30) |
| `JWT_ACCESS_MINUTES` | Hayır | Access token ömrü (varsayılan: 15) |
| `JWT_REFRESH_DAYS` | Hayır | Refresh token ömrü (varsayılan: 7) |

> \* En az bir LLM API anahtarı gereklidir.

```bash
# JWT_SECRET üret
make secret
# veya: python -c "import secrets; print(secrets.token_hex(64))"
```

---

## API Kullanımı

### Kimlik Doğrulama

```bash
# Kayıt
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "guclu-parola-123"}'

# Giriş
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"email": "you@example.com", "password": "guclu-parola-123"}'
# → {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}

# Token yenile (rotasyon — eski token geçersiz olur)
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -d '{"refresh_token": "..."}'

# Tüm oturumları kapat
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

### Proje Oluşturma

```bash
# Async (hemen job_id döner)
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "E-ticaret Platformu", "description": "React + FastAPI", "async_mode": true}'
# → {"job_id": "abc123", "status": "queued"}

# Durum sorgula
curl http://localhost:8000/api/v1/projects/abc123/status \
  -H "Authorization: Bearer <token>"
```

### Kalite & Onay

```bash
curl http://localhost:8000/api/v1/quality/summary       # proje kalite özeti
curl http://localhost:8000/api/v1/quality/agents        # ajan bazlı dağılım
curl http://localhost:8000/api/v1/approvals/pending     # bekleyen onaylar
curl -X POST http://localhost:8000/api/v1/approvals/{id}/decide \
  -d '{"approve": true, "decided_by": "lead"}'
```

### Gözlemlenebilirlik

```bash
curl http://localhost:8000/api/v1/heal/report    # ajan sağlık raporu
curl http://localhost:8000/api/v1/metrics        # p50/p95/p99 metrikler
wscat -c "ws://localhost:8000/ws?token=<token>"  # canlı olaylar (WebSocket)
```

---

## Celery Görev Kuyruğu

```bash
make celery           # worker başlat
make celery-beat      # zamanlanmış görevler
make celery-monitor   # olayları izle

# Kuyruk öncelikleri
# critical  → heal engine kontrolleri
# default   → proje görevleri
# background→ webhook, bellek temizliği
```

---

## Test

```bash
make test               # tüm testler
make test-cov           # kapsam raporu (htmlcov/index.html)

pytest tests/test_review_fixes.py -v    # inceleme düzeltme testleri
pytest tests/test_faz3.py -v            # kalite sistemi testleri
pytest tests/test_heal_system.py -v     # öz-iyileştirme testleri
```

**Test kategorileri:**

| Dosya | Kapsam |
|-------|--------|
| `test_suite.py` | MMR, orchestrator, job queue, rate limiter |
| `test_heal_system.py` | FSM, recovery stratejileri, root cause |
| `test_faz3.py` | Kalite sistemi, approval gate, memory |
| `test_review_fixes.py` | Auth negatif senaryolar, 429, webhook HMAC, deque |

---

## Güvenlik

### JWT
- Access token: **15 dk** | Refresh token: **7 gün** (rotasyon, revocation)
- Secret: **min 64 karakter** (OWASP HS256 — `make secret`)
- Zamanlama saldırısı koruması: kullanıcı bulunamasa da bcrypt çalışır

### CORS
`allow_credentials=True` ile wildcard **kullanılmaz** — spesifik metodlar/başlıklar zorunlu:
```env
ALLOWED_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
ALLOWED_HEADERS=Authorization,Content-Type,X-Trace-ID
```

### Rate Limiting
- Redis varsa → dağıtık sliding window (çok-worker)
- Redis yoksa → in-memory fallback
- Global: 200/dk | Proje oluşturma: 10/dk | Giriş: 5/dk

### Webhook
HMAC-SHA256 imzası + `hmac.compare_digest()` (timing-safe)

```bash
make security   # Bandit + pip-audit CVE taraması
```

---

## Dağıtım (Üretim)

**Kontrol listesi:**
- [ ] `ENVIRONMENT=production`
- [ ] `JWT_SECRET` ≥ 64 karakter
- [ ] `ALLOWED_ORIGINS` üretim domain'i
- [ ] HTTPS aktif (Nginx / Caddy)
- [ ] `make migrate` çalıştırıldı
- [ ] `REDIS_URL` ayarlı (dağıtık rate limiter)

```bash
# Gunicorn + Uvicorn (CPU*2+1 worker önerilir)
gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 9 \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

---

## Geliştirici Araçları

```bash
make lint       # Ruff kod analizi
make format     # Ruff otomatik biçimlendirme
make security   # Bandit + pip-audit
make secret     # JWT_SECRET üret
make clean      # __pycache__ temizle
```
