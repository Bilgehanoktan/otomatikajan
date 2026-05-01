# Infrastructure Readiness Audit (PRMR-01)

**Tarih:** 2026-05-01T17:48:34.877220Z
**Faz:** 1 (Readiness Audit)
**Durum:** [FAIL]
**Standby Condition:** [LOCKED] ACTIVE (Waiting for Trigger)

## 1.1 Baglanti Kontrolleri

| Servis | Hedef | Durum | Hata Mesaji / Not |
|--------|-------|-------|-------------------|
| **PostgreSQL** | `127.0.0.1:5433/ai_company` | [FAIL] | [Errno 111] Connection refused |
| **Redis** | `127.0.0.1:6380/0` | [FAIL] | [Errno 111] Connection refused |
| **Celery Broker** | `Redis` bagimli | [FAIL] | Redis bagimli |
| **pgvector** | PostgreSQL eklentisi | [BLOCKED] | DB erisimi olmadigi icin kontrol edilemedi |
| **Docker Daemon** | `dockerDesktopLinuxEngine` | [FAIL] | `Sistem belirtilen dosyayi bulamiyor` (Daemon kapali olabilir) |

## 1.2 Sema Hazirligi

* Primary DB'ye erisilemediginden sema hazirligi, migration butunlugu ve tablo kontrolleri **yapilamamistir**.

## Sonuc

Primary altyapi bilesenlerinin (Postgres ve Redis) fiziksel olarak kapali oldugu veya ag katmaninda ulasilamadigi tespit edilmistir. Docker Desktop servislerinin calismadigi degerlendirilmektedir. Bu durum, PRMR-01 uygulama planinin Faz 1 "No-Return Gate" politikasina takilmistir.

**Aksiyon:** Operasyon gecici olarak durdurulmali ve `no_return_gate_decision.md` raporu yayinlanmalidir. Sistem **Stable Degraded (SQLite)** modda kalmaya devam etmelidir.

## Faz 2 Yol Haritasi

**Amac:** `local-dev` profilinde ayaga kalkan sistemin UI/API sozlesmesi, yetkilendirme akisi ve opsiyonel entegrasyonlar acisindan stabil hale getirilmesi.

### Hedefler

- Control plane ile `apps.public_api.main` arasinda tekil ve kanonik API sozlesmesi netlestirilecek.
- Frontend tarafinda kalan legacy alias path kullanimi kaldirilacak, ekranlar kanonik route'lara baglanacak.
- `incidents`, `proof snapshots`, `audit bundles` ve `event stream` icin auth'lu smoke testleri kalici hale getirilecek.
- i18n mesaj anahtarlari, locale fallback ve eksik ceviri alanlari tamamlanacak.
- `TELEGRAM_ENABLED` ve `DEERFLOW_ENABLED` icin wiring, import ve fallback davranislari canli senaryolarla dogrulanacak.

### Cikis Kriterleri

- `local-dev` modunda kritik yonetim ekranlari 500 ve 404 hatasi vermeyecek.
- Login sonrasi temel governance ve workflow ekranlari veri gosterecek.
- Kanonik API path'lerini kullanan smoke test paketi yesil olacak.
- Control plane ile public API arasinda yeni bir contract drift gozlenmeyecek.

## Faz 3 Yol Haritasi

**Amac:** `full-stack-local` profilini tam kapasiteyle calistirip Redis, Postgres, Celery ve DeerFlow zincirini operasyona hazir seviyede dogrulamak.

### Hedefler

- Docker daemon acikken `BASLAT.bat fullstack` ile tum servis topolojisi deterministik bicimde ayaga kaldirilacak.
- `QUEUE_BACKEND=celery` altinda worker registration, queue dispatch, retry ve completion akislari uctan uca test edilecek.
- Redis, Postgres, Celery worker, Celery beat ve DeerFlow bridge icin readiness ve health kontrolleri sertlestirilecek.
- Primary DB migration, schema butunlugu ve kritik tablo hazirligi dogrulanacak.
- Governance, workflow ve repair akislari in-process yerine gercek queue altyapisi ustunde calistigi kanitlanacak.

### Operasyonel Dogrulama

- Workflow create -> queue dispatch -> worker execution -> event emission zinciri canli smoke ile dogrulanacak.
- Approval, incident ve proof kayitlarinin primary DB'ye dustugu teyit edilecek.
- DeerFlow routing, timeout ve fallback davranislari kontrollu senaryolarla olculecek.
- Scheduler veya beat tetiklerinin beklenen isleri planlandigi sekilde calistirdigi dogrulanacak.

### Cikis Kriterleri

- `full-stack-local` modunda ana servisler healthy durumda gorunecek.
- En az bir ornek workflow Celery hattindan basariyla tamamlanacak.
- Redis ve Postgres bagimliliginda degraded fallback yerine primary stack aktif olacak.
- PRMR-01 readiness kontrolu, Docker destekli senaryoda PASS seviyesine yukselecek.
