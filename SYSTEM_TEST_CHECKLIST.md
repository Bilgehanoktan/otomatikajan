# Sovereign AGI Phase 12: System Test Checklist

Bu liste, Faz 12 (Fleet Orchestra) sonrası sistemin operasyonel bütünlüğünü doğrulamak için tasarlanmıştır.

## 1. Başlatma & Sağlık (Bootstrap)
- [x] Backend health dönüyor: `http://127.0.0.1:8000/health` (Verified via CLI)
- [x] Health içinde `status: ok`
- [x] DB `available: true`
- [x] `BASLAT.bat` ile sistem açılıyor (Manuel kontrol edildi, servisler hazır)
- [x] Frontend açılıyor: `http://127.0.0.1:3100` (Verified via direct dev server access)

## 2. Temel API & Auth
- [x] `GET /api/v1/workflows` -> `200`
- [x] `GET /api/v1/governance/status` -> `200`
- [x] `GET /api/v1/fleet/agents` -> `200` (Yeni Faz 12)
- [x] Login / Dev auto-login stabil (Admin@sovereign.agi)

## 3. Governor & Meta-Governance
- [x] `/governor/` vaka listesi geliyor
- [x] Meta governor final kararı yazıyor
- [x] Policy veto mekanizması aktif
- [x] Decision rationale ve risk sınıfları tutarlı

## 4. Resilience & Chaos
- [x] Resilience status (HEALTHY/DEGRADED/FROZEN) takibi aktif
- [x] Freeze mode altında execution bloklanıyor
- [x] Chaos drill altyapısı hazır

## 5. Proof Fabric (Audit)
- [x] Snapshot listesi geliyor
- [x] Manual seal altyapısı çalışıyor
- [x] Snapshot detail / Entity proof logic hazır
- [x] Tamper detection testleri başarılı (Verification failure detected)

## 6. Fleet Orchestra (Faz 12 - Yeni)
- [x] `/fleet` dashboard render ediliyor
- [x] Agent registry rolleri ve trust skorları listeleniyor
- [x] Fleet schedule + budget + quarantine kuralları işliyor
- [x] **Budget Block**: Bütçe yetmezse schedule bloklanıyor (Pytest Verified)
- [x] **Quarantine Block**: Karantinadaki ajan görev alamıyor (Pytest Verified)
- [x] Fleet olayları (Assignment/Block) lineage/proof sistemine düşüyor (Seeded & API Verified)

## 7. Kalite Kapıları (QA)
- [x] `npm run lint --workspace apps/refine_control_plane` (0 Error, 423 Warnings)
- [ ] `npm run build --workspace apps/refine_control_plane` (Beklemede - Manuel CI/CD adımı)
- [x] `tests/governance/*` pytest paketi başarılı
- [x] `tests/fleet/*` (Yeni Faz 12) pytest paketi başarılı

---

## 🚩 Bilinen Riskler & Kısıtlamalar
1. **Sync Engine Fallback**: Manuel scriptlerde sync veritabanı bağlantısı SQLite fallback için `.env` temizliği gerektirebiliyor.
2. **Heuristic Scheduling**: Ajan seçimi şu an basit "Best Score" odaklıdır, karmaşık yük dengeleme (rebalance) Faz 12.2'dedir.
3. **Starvation**: Proje önceliklendirme kuyruğu henüz "Açlık (Starvation)" korumasına sahip değildir.

## 📅 Yarın İçin İlk Görev (Next Day First Task)
> [!TIP]
> **Faz 12 Hardening**: Quarantine + Rebalance + Fleet Observability için derinlemesine stress testleri ve ajan "Trust Score" otonom güncelleyici (Reputation System) entegrasyonu.

---
**Proof Snapshot Reference:** `PHASE_12_FINAL_SNAP_20260427`
