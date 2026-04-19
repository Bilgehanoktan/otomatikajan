# Egemen YAZ - Degraded Mode ve Kurtarma (Recovery) Runbook'u

**Sürüm:** v1.0  |  **Sahip:** EGEMEN / Platform Operations  |  **Durum:** AKTİF  |  **Son Güncelleme:** 2026-04-18  |  **Kapsam:** Resilient Mode, SQLite Fallback, In-Process Workers, Database Migration

> [!IMPORTANT]
> **Bağlantılı Dokümanlar:** [logging.md](logging.md), [ops_runbook.md](../ops_runbook.md), [global_failover_runbook.md](../global_failover_runbook.md)

---

## 1. Amaç
Bu runbook, Egemen YAZ platformunun ana altyapı bileşenlerinde (PostgreSQL, Redis vb.) kesinti yaşandığında devreye giren "Degraded Mode" (Kısıtlı Durum) operasyonlarını yönetmek ve sistem normale döndüğünde güvenli kurtarma (recovery) sürecini icra etmek için hazırlanmıştır.

## 2. Stable Degraded Modu Tanımı
Sistem aşağıdaki durumlarda "Stable Degraded" kabul edilir:
*   **Ana Veritabanı (Postgres) Erişilemez:** Sistem verileri `cortex_local.db` (SQLite) üzerine yazmaya/okumaya devam edebiliyor.
*   **Redis/Celery Erişilemez:** Arka plan işleri "In-Process Worker" (Thread/Process) moduyla uygulama içinde kısıtlı kapasiteyle yürüyor.
*   **Veri Bütünlüğü:** Kritik olmayan telemetri verileri kaybolsa dahi, ana workflow durumu korunabiliyor.

## 3. Fallback Tespiti ve Doğrulama
Operatör, sistemin fallback durumunda olduğunu şu şekilde anlar:

### A. SQLite Fallback (Resilient Mode)
*   **Kontrol:** `runtime/data/` dizininde `cortex_local.db` dosyasının update zamanını (write) kontrol edin.
*   **Log Sinyali:** `[db] [WARNING] Primary DB unavailable, falling back to SQLite.`

### B. In-Process Worker Doğrulama
*   **Kontrol:** Celery container'ları ölü/bağlantısız olmasına rağmen ana API loglarında `[worker] [INFO] Processing task in-process: <task_id>` satırlarını görün.
*   **Anlamı:** Kuyruk sistemi devreden çıkmış, işler o anki API süreci içinde senkron/asenkron Thread ile yürütülüyordur.

## 4. İzleme Kanalları (Headers & Logs)
Degraded mode sırasında teşhis için şu kanalları kullanın:
*   **HTTP Response Headers:**
    *   `X-System-Status: degraded` -> Sistem fallback modda çalışıyor.
    *   `X-System-Reason: database_unavailable` -> Postgres kesintisi.
*   **Kritik Loglar:**
    *   `domain_event_logs` (SQLite tarafındaki) tablosuna düşen hata kodlarını izleyin.
    *   Terminalden `Fallback session started` mesajını arayın.

## 5. Emergency Rollback (Ne Zaman Durdurulmalı?)
Aşağıdaki durumlarda degraded operasyon durdurulmalı ve tam sistem yedeğine (Snapshot) dönülmelidir:
*   SQLite dosyası (`cortex_local.db`) "Database Disk Image is Malformed" hatası veriyorsa.
*   In-process worker bellek tüketimi (Leak) nedeniyle ana API'yi çökertecek seviyeye (RAM > %85) geldiyse.
*   Workflow durumları (status mismatch) SQLite ve API belleği arasında senkronizasyonu tamamen yitirdiyse.

## 6. Kurtarma Hazırlığı (Checklist)
Postgres ve Redis servisleri ayağa kalktığında, geri dönüşten ÖNCE şunları doğrulayın:
- [ ] Postgres servisi erişilebilir (Port 5432 aktif).
- [ ] Redis ping yanıtı veriyor.
- [ ] SQLite dosyasının bütünlüğü kontrol edildi (`sqlite3 .integrity_check`).
- [ ] Bekleyen (Pending) in-process worker işi kalmadı.

## 7. Geri Dönüş Akışı (Transition Sequence)

Sistemi normale döndürmek için şu sırayı takip edin:

1.  **Sistemi Freeze Et:** API'yi servis dışı bırak veya yazma işlemlerini askıya al.
2.  **Snapshot Al:** Mevcut `cortex_local.db` dosyasının bir kopyasını `.backup` klasörüne al.
3.  **Integrity Check:** SQLite yedeğinin bozuk olmadığından emin ol.
4.  **Data Synchronization:** `migrate_v13.py` veya projedeki ilgili sync scripti ile SQLite üzerindeki "degraded dönem" verilerini ana Postgres'e aktar.
5.  **Re-connect:** `.env` dosyasında ana DB bağlantılarını doğrula ve API/Worker servislerini restart et.
6.  **Verify:** `X-System-Status` header'ının `ok` değerine döndüğünü ve Celery'nin iş aldığını onayla.

## 8. Sık Kullanılan Komutlar
**SQLite Bütünlük Kontrolü:**
```bash
sqlite3 runtime/data/cortex_local.db "PRAGMA integrity_check;"
```

**Sync Script Çalıştırma (Örnek):**
```bash
python scripts/migrate_local_to_primary.py --commit
```

---

## 10. Operasyonel Özet
"Degraded mode hayat kurtarır ancak veri biriktirme sınırı vardır. Postgres/Redis geri geldiğinde 'Snapshot -> Sync -> Restart' sırası bozulmamalıdır. Aktarım başarısız olursa SQLite yedeğinden elle kurtarma ana senaryodur."
