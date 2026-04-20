# Checklist: Primary Infrastructure Transition (SQLite -> Postgres/Redis)

## [x] Faz 0: Pre-Flight (Queue Drain & Dedup Audit)
- [x] Otonom görev kuyrukları için tahliye (queue drain) işlemi tamamlanmalı.
- [x] Duplicate-execution (çifte çalıştırma) engelleme mekanizması denetlenmeli.
- [x] Duplicate guard raporu operasyon loguna (Audit Bundle) eklenmeli.

## [x] Faz 1: Sağlık & Bağlantı Doğrulama
- [x] Postgres servisine TCP/IP erişimi doğrulanmalı.
- [x] Redis cluster durumu `READY` olarak teyit edilmeli.
- [x] CloudRun/K8s sidecar'lar üzerinden connectivity testi tamamlanmalı.
- [x] Publish/consume smoke test ve write smoke test başarıyla tamamlanmalı.

## [x] Faz 2: Veri Bütünlüğü (Pre-Migration)
- [x] SQLite veritabanının fiziksel snapshot'ı alınmalı (`libs.db.bak`).
- [x] `decision_lineage` mühürlerinin geçerliliği kontrol edilmeli.
- [x] Bekleyen (pending) otonom görevlerin listesi dökülmeli.

## [x] Faz 3: Senkronizasyon (Execution)
- [x] `MIGRATE_TO_PRIMARY` komutu ile veri aktarımı başlatılmalı.
- [x] Veri aktarım loglarında "0 errors" görülmeli.
- [x] `policy_registry` Baseline-v10.2 konfigürasyonu Postgres'te doğrulanmalı.

## [x] Faz 4: Devreye Alma & Doğrulama
- [x] API Pointer Postgres'e çevrilmeli.
- [x] Dashboard üzerinden "Live Telemetry" akışı teyit edilmeli.
- [x] Birinci seviye bir onay döngüsü başarıyla tamamlanmalı.
- [x] T+15m Checkpoint: Tüm alt sistemlerde stabilite yeniden ölçülmeli.

---
> [!IMPORTANT]
> Herhangi bir Faz'da hata alınması durumunda "ROLLBACK TO SQLITE" protokolu (RB-DEG-01) derhal işletilir.
