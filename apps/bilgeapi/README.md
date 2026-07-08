# BilgeAPI — Standalone Package

BilgeAPI, otonom olay yönetimi, teşhis ve onarım taleplerini yöneten, bağımsız ve taşınabilir (portable) bir API servisidir.

## Özellikler

* **Incident / Diagnostic / Repair Orchestration**: Olay kabulü, teşhis adımları ve onarım talebi yönetimi.
* **Governance**: Politika motoru (`policy_engine.py`), risk analizi, onay mekanizmaları ve denetim günlüğü (`audit_logger.py`).
* **Safe Intervention**: Dosya müdahale güvenliği (`PathGuard`, `RollbackManager`, `QuarantineManager`).
* **Webhooks & Integrations**: HMAC-SHA256 imzalı webhook, SSRF guard ve Slack/Teams/GitHub/Jira/Telegram entegrasyonu.
* **Durable Queue**: SQLite/Postgres tabanlı ve opsiyonel Celery/Redis destekli dayanıklı kuyruk modelleri.
* **Security & Auth**: RBAC (Sovereign Prime, Admin, Operator, Observer) ve API Key / JWT yetkilendirmesi.

---

## Kurulum ve Çalıştırma

### 1. Bağımlılıkları Yükleyin

Paket Python >= 3.12 gerektirir:

```bash
pip install -r requirements.txt
```

### 2. Yapılandırma Dosyasını Hazırlayın

`.env.example` dosyasını `.env` olarak kopyalayın ve gerekli değerleri doldurun:

```bash
cp .env.example .env
```

### 3. Veri Tabanı Migrasyonlarını Çalıştırın

Alembic ile veritabanı tablolarını oluşturun (PostgreSQL veya SQLite fallback):

```bash
alembic -c alembic.ini upgrade head
```

### 4. Uygulamayı Başlatın

FastAPI sunucusunu uvicorn ile başlatın:

```bash
uvicorn bilgeapi.main:app --host 0.0.0.0 --port 8100
```

---

## Sağlık Kontrolü ve API Dokümantasyonu

API başladıktan sonra şu adreslerden kontrolleri yapabilirsiniz:

* **Sağlık Kontrolü**: `http://localhost:8100/health` (veya `/v1/catalog`)
* **OpenAPI Şeması**: `http://localhost:8100/openapi.json`
* **Swagger Arayüzü**: `http://localhost:8100/docs`
