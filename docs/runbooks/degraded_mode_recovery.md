# Runbook: RB-DEG-01 — Degraded Mode & Recovery Protocol

## 1. Operasyonel Bağlam
Sovereign AGI sistemi (Egemen YAZ), birincil veri ve mesajlaşma katmanları (Postgres/Redis) erişilemez olduğunda "Degraded Mode" (Düşük Kapasiteli Çalışma Modu) üzerinden operasyonlarını sürdürmek üzere tasarlanmıştır. Bu modda sistem, yerel SQLite veritabanı ve in-memory kuyruklar ile otoriter çalışmaya devam eder.

## 2. Degraded Mode Operasyon Kuralları
- **Baseline:** Yalnızca onaylı versiyonlar (Şu an: **Baseline-v10.2**) kullanılır.
- **Persistence:** Tüm kararlar yerel `libs.db` (SQLite) üzerinde mühürlenir.
- **Lineage:** Karar soyağacı (decision lineage) kesintisiz devam eder. Primary ayağa kalktığında bu kayıtlar bulk-sync ile aktarılacaktır.

## 3. Recovery Phase: SQLite -> Postgres/Redis

### A. Hazırlık (Kritik)
1. **Primary Sync Check:** Postgres bağlantısının `HEALTH_OK` olduğu doğrulanmalı.
2. **Persistence Freeze:** Sisteme yeni görev girişi geçici olarak (T-15m) durdurulur (`DRAIN_MODE`).
3. **Lineage Sealing:** SQLite üzerindeki son 24-72 saatlik tüm `governance_lineage` ve `audit_trail` kayıtları mühürlenir.

### B. Execution Sequence (Dönüş Protokolü)
1. **Schema Validation:** Postgres şeması ile mevcut SQLite şeması `alembic` üzerinden senkronize edilir.
2. **Data Migration:**
   - `repair_memory` -> Postgres
   - `policy_registry` -> Postgres (Active parameters)
   - `decision_lineage` -> Postgres
3. **System Re-point:** `libs.db.session` üzerinden master pointer Postgres'e çevrilir.
4. **Resiliency Test:** T-0'da bir "Self-Test" görevi koşturulur.

## 4. Emergency Rollback (Dönüş Başarısız Olursa)
Dönüş sırasında herhangi bir `DataIntegrityError` veya `ConnectivityLoss` yaşanırsa, sistem derhal **SQLite Otoriter Moduna** geri döner.

---
**Author:** Sovereign Architect  
**Status:** AUTHORITATIVE (BASELINE-V10.2 READY)  
**ID:** RB-DEG-01
