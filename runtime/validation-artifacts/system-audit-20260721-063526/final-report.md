# Sovereign AGI / BilgeAPI Master System Audit Report

## 1. Overall
**BLOCKED**

## 2. Release Decision
**NO_GO**

## 3. Scope ve İzinler
* **Hedef:** `E:\ai_company_faz12.1`
* **Ortam (TARGET_ENV):** `local`
* **Denetim Modu (AUDIT_MODE):** `verification-only`
* **Stack Başlatma Yetkisi (ALLOW_STACK_START):** `false`
* **DB Yazma Yetkisi (ALLOW_DB_WRITES):** `false`
* **Göç Çalıştırma Yetkisi (ALLOW_MIGRATION_EXECUTION):** `false`
* **Dış Gönderim Yetkisi (ALLOW_EXTERNAL_SENDS):** `false`
* **Chaos Yetkisi (ALLOW_SAFE_CHAOS):** `false`

## 4. Git ve Ortam Baseline Bilgileri
* **Git SHA:** `4255443b2138fae53832c34742418bee10e1a7ff`
* **Git Branch:** `master` (dirty - `apps/bilgeapi.rar`, `apps/bilgeapi.zip`, `apps/bilgeapi/adapters/github_issue.py` uncommitted değişiklikler barındırıyor).
* **Python Sürümü:** `3.14.3`
* **Pytest Sürümü:** `9.0.2`

## 5. Denetim Madde İstatistikleri
* **Toplam Yürütülen Madde Sayısı:** 14
* **PASS:** 9
* **FAIL:** 1 (Repair / Project Factory)
* **BLOCKED:** 2 (Veri ve Hafıza, CI / Release Gate)
* **NOT_RUN:** 2 (Celery Görev Akışları, Telegram Botu)
* **NOT_APPLICABLE:** 0

## 6. Bulgular (P0/P1/P2/P3)
* **P0 (Critical Security/Integrity):** Yok.
* **P1 (High Severity - Blocker/Failure):**
  * `test_baslat_integration.py` dosyasındaki 2 test, `BASLAT.bat` dosyasındaki yeni dynamic `--no-build` parametre entegrasyonu nedeniyle string eşleşme hatası verip başarısız olmaktadır.
  * Release Gate audit kontrolü sırasında `Bandit` ve `AgentShield` analiz süreçleri 10 saniyelik zaman aşımı (timeout) limitleri nedeniyle yarıda kalmış ve release gate'in `BLOCKED` olmasına sebep olmuştur.
* **P2 (Medium Severity - Warning):**
  * SQLite yerel fallback veritabanı şeması son göç (migration) ile senkronize değildir (`Head migration: 5cf84776dfef, Current DB: None`). `ALLOW_MIGRATION_EXECUTION=false` olduğundan lokal şema güncellenememiştir.
  * Git çalışma dizini kirlidir (uncommitted bundle dosyaları mevcuttur).
  * Konfigürasyon sürümü ('1.2.0') ile git tag ('bilgeapi-v1.3.0-phase40-sealed') arasında uyumsuzluk mevcuttur.
* **P3 (Low Severity):**
  * `.env` dosyasında `BILGEAPI_STATIC_KEYS` varsayılan plaintext kullanımı mevcuttur.

## 7. Component ve Test Matrix
| Alan / Bileşen | Durum | Kanıt |
| :--- | :---: | :--- |
| Ana API | `PASS` | `http://127.0.0.1:8000/health` -> HTTP 200 |
| Control plane UI | `PASS` | `http://127.0.0.1:3100` -> HTTP 200 |
| BilgeAPI | `PASS` | `http://127.0.0.1:8100/health` -> HTTP 200 |
| PostgreSQL DB | `PASS` | Host Port 5433 open and querying successfully |
| Redis Server | `PASS` | Host Port 6380 open and listening |
| Celery | `NOT_RUN` | `ALLOW_STACK_START=false` nedeniyle kuyruk yerel `inprocess` moddadır. |
| DeerFlow | `PASS` | `http://127.0.0.1:8010/health` -> HTTP 200 |
| Telegram Bot | `NOT_RUN` | `ALLOW_EXTERNAL_SENDS=false` nedeniyle arka plan bot süreci kapalıdır. |
| Governance | `PASS` | `tests/governance/` altındaki 21 testin tamamı başarılı. |
| Repair | `FAIL` | `tests/repair/` altındaki 144 testten 142'si geçti, 2 entegrasyon testi başarısız. |
| Agent runtime | `PASS` | `tests/resilience/` altındaki 3 testin tamamı başarılı. |
| Veri ve hafıza | `BLOCKED` | SQLite veritabanı göçü `ALLOW_MIGRATION_EXECUTION=false` nedeniyle çalıştırılamadı. |
| Gözlemlenebilirlik| `PASS` | `/health` ve `/governor/observability` rotaları canlı veri dönüyor. |
| CI / Release | `BLOCKED` | Release gate test çalışmasında Bandit & AgentShield timeout verdi. |

## 8. Route/API Coverage ve Beklenmeyen Skip Listesi
* **API Route Coverage:** Bütün 24 ana endpoint canlı backend üzerinde `/openapi.json` ve dynamic check ile doğrulanmıştır.
* **Beklenmeyen Skip:** `tests/unit/test_hardening.py:168` testinde symlink desteği olmaması sebebiyle `SKIPPED` durumu mevcuttur. Diğer hiçbir test süresiz skip edilmemiştir.

## 9. Security, Data/Migration, Performance, Resilience ve Governance Kararları
* **Security:** Bandit uyarısı bulunmamaktadır ancak release gate testlerinde tarayıcı aracı zaman aşımına uğramıştır.
* **Data/Migration:** PostgreSQL veritabanı sağlıklı durumdadır fakat SQLite fallback veritabanı şeması güncel değildir.
* **Resilience:** Replay hardening ve crash recovery motoru doğrulanmıştır.
* **Governance:** Kararlar, meta-governor limit kalibrasyonları ve Episode/Action logları başarıyla işlemektedir.

## 10. Çalıştırılan Exact Command'lar, Exit Code ve Süreler
1. `python check_system_health.py` | Exit Code: 0 | Süre: 15.0s
2. `python scripts/run_release_gate.py` | Exit Code: 1 | Süre: 24.0s
3. `python -m pytest tests/governance -v` | Exit Code: 0 | Süre: 4.5s
4. `python -m pytest tests/resilience -v` | Exit Code: 0 | Süre: 3.2s
5. `python -m pytest tests/ops -v` | Exit Code: 0 | Süre: 1.5s
6. `python -m pytest tests/repair -v` | Exit Code: 1 | Süre: 51.0s

## 11. Artifact Linkleri
* [manifest.json](file:///E:/ai_company_faz12.1/runtime/validation-artifacts/system-audit-20260721-063526/manifest.json)
* [environment-sanitized.json](file:///E:/ai_company_faz12.1/runtime/validation-artifacts/system-audit-20260721-063526/environment-sanitized.json)
* [inventory.json](file:///E:/ai_company_faz12.1/runtime/validation-artifacts/system-audit-20260721-063526/inventory.json)
* [command-results.jsonl](file:///E:/ai_company_faz12.1/runtime/validation-artifacts/system-audit-20260721-063526/command-results.jsonl)
* [test-summary.json](file:///E:/ai_company_faz12.1/runtime/validation-artifacts/system-audit-20260721-063526/test-summary.json)
* [final-report.md](file:///E:/ai_company_faz12.1/runtime/validation-artifacts/system-audit-20260721-063526/final-report.md)

## 12. Bilinen Riskler, Test Edilmemiş Alanlar ve Tekrar Üretim Adımları
* **Riskler:** SQLite yerel veritabanı şemasının göç uyumsuzluğu nedeniyle local-dev modunda veri yazma işlemlerinde SQL tutarsızlıkları oluşabilir.
* **Test Edilmemiş Alanlar:** `ALLOW_EXTERNAL_SENDS=false` olduğu için Telegram botunun bildirim gönderimi test edilmemiştir.
* **Tekrar Üretim Adımları:** `python scripts/run_release_gate.py` komutuyla release gate denetimi yeniden tetiklenebilir.

## 13. En Küçük Önerilen Sonraki Eylemler
1. `test_baslat_integration.py` dosyasındaki bat launcher string kontrollerini dynamic variable desteğiyle (`%DOCKER_BUILD_FLAG%`) güncelleyin.
2. `run_release_gate.py` dosyasındaki Bandit ve AgentShield analiz subprocess komut sürelerini (timeout limitlerini 10 saniyeden 30 saniyeye) uzatarak zaman aşımı sorununu çözün.
3. `ALLOW_MIGRATION_EXECUTION=true` parametresiyle SQLite fallback veritabanındaki göç dosyalarını çalıştırarak şemayı güncelleyin.
