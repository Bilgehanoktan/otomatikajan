# Checklist: Primary Infrastructure Transition (SQLite -> Postgres/Redis)

## [ ] Faz 1: Sağlık & Bağlantı Doğrulama
- [ ] Postgres servisine TCP/IP erişimi doğrulanmalı.
- [ ] Redis cluster durumu `READY` olarak teyit edilmeli.
- [ ] CloudRun/K8s sidecar'lar üzerinden connectivity testi tamamlanmalı.

## [ ] Faz 2: Veri Bütünlüğü (Pre-Migration)
- [ ] SQLite veritabanının fiziksel snapshot'ı alınmalı (`libs.db.bak`).
- [ ] `decision_lineage` mühürlerinin geçerliliği kontrol edilmeli.
- [ ] Bekleyen (pending) otonom görevlerin listesi dökülmeli.

## [ ] Faz 3: Senkronizasyon (Execution)
- [ ] `MIGRATE_TO_PRIMARY` komutu ile veri aktarımı başlatılmalı.
- [ ] Veri aktarım loglarında "0 errors" görülmeli.
- [ ] `policy_registry` Baseline-v10.2 konfigürasyonu Postgres'te doğrulanmalı.

## [ ] Faz 4: Devreye Alma & Doğrulama
- [ ] API Pointer Postgres'e çevrilmeli.
- [ ] Dashboard üzerinden "Live Telemetry" akışı teyit edilmeli.
- [ ] Birinci seviye bir onay döngüsü başarıyla tamamlanmalı.

---
> [!IMPORTANT]
> Herhangi bir Faz'da hata alınması durumunda "ROLLBACK TO SQLITE" protokolu (RB-DEG-01) derhal işletilir.
