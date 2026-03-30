# RC1 — Release Candidate 1 Changelog

## Faz 12 RC1 (Sprint 1-4)

### Sprint 1 — Test ve Doğrulama Omurgası
- **tests/conftest.py**: `importlib.util.find_spec()` ile scoped stub yönetimi; gerçek paket varsa stub yüklenmiyor, test bitince temizleniyor
- **repair/schemas/repair_job.py**: RC1 yeni alanlar eklendi: `vector_context_used`, `debate_triggered`, `sandbox_verified`, `lesson_saved`, `ranker_adjusted`, `ranker_adjusted_confidence`, `sandbox_output`. Yeni state'ler: `VECTOR_CONTEXT_LOADED`, `GENERATED_TESTS_READY`, `SANDBOX_VERIFIED`, `LESSON_SAVED`
- **repair/verification/verification_engine.py**: `save_validation_report()` ve `get_validation_report()` eklendi — gerçek kanıt zinciri kalıcı store'a kaydediliyor
- **api/repair_router.py**: `/jobs/{job_id}/validation` endpoint'i gerçek rapor dönüyor (önce store, yoksa job state'den türet)

### Sprint 2 — Faz 12 Pipeline Entegrasyonu
- **core/repair_orchestrator.py**: 16 adımlı RC1 pipeline: Fingerprint → Vector RAG → Triage → Policy → Root Cause → Ranker RC1 → Debate (koşullu) → Patch Plan → Generated Tests → Patch Generate → Review → Architecture Guard → Verify RC1 → Sandbox Verify → Risk Score → Canary RC1 → Policy Gate → PR Proposal → Metrics → Vector Lesson Save
- **Debate Engine**: ±5% içindeki hipotezler otomatik debate tetikliyor; `job.debate_triggered`, `job.debate_result_summary`, `job.debate_winning_hypothesis` doluyor
- **Canary RC1**: risk bazlı — low(<70) otomatik, high(≥70) manual review
- **Validation RC1**: verify() anında `save_validation_report(job_id)` çağırıyor

### Sprint 3 — Legacy Uyumluluk ve Modülerleşme
- **api/task_router.py**: Compatibility Shim — `TaskCreateRequest` re-export, Faz 4/7 testleri kırılmıyor
- **llm/model_orchestrator.py**: `ProviderStats.maybe_half_open()` compat metodu eklendi
- **api/rate_limiter.py**: `reset()` → `float` dönüş tipi (legacy test kontratı)
- **llm/cost_calc.py**: Saf maliyet hesaplama, DB bağımlılığı yok; `calculate_cost()`, `estimate_tokens()`, `format_cost()`, `budget_check()`
- **llm/cost_tracker.py**: `cost_calc`'a delege, lazy DB import
- **memory/store.py**: Top-level ağır import kaldırıldı (zaten lazy'di)
- **api/repair_admin_router.py**: `/lessons` ve `/lessons/stats` endpoint eklendi

### Sprint 4 — Repo Temizliği ve Release Sertleştirme
- `*.pyc` / `__pycache__` / `.pytest_cache` temizlendi
- `main.py`: 12 aktif router, deprecated improvement_router kaldırıldı
- `.gitignore`: `.env` dahil

### Hardening Phase — Deep System Audit (Latest)
- **main.py**: `JWT_SECRET` için production'da minimum 64 karakter zorunluluğu eklendi (P0 Security).
- **main.py**: `system_watchdog_supervisor` kontrol periyodu 60 saniyeden 15 saniyeye düşürüldü (Daha hızlı kurtarma).
- **core/task_management.py**: `system_controller` ajanı `AGENT_CONTRACTS` içerisine eklendi; artık proje planlamalarında sistem kontrolü subtask olarak atanabiliyor.
- **tests/test_core_parities.py**: Yeni regresyon ve entegrasyon test seti oluşturuldu. 
  - Startup/Lifecycle, Config Precedence, Monitoring DB Failure, Sandbox Production Security, Worker Error Status senaryoları kapsandı.
- **core/ceo_engine.py**: `llm_cost_logs` tablosu eksikse budget check'in sessizce atlanması sağlandı (Migration bekleme toleransı).

### Sprint 6 — Self-Repair Hydration & Platform Stabilization (Faz 12.1)
- **Hafıza Geri Yükleme (Hydration)**: `IncidentMemory` ve `IncidentIngestor` için DB tabanlı hydration implemente edildi; sistem restart sonrası olaylar kaybolmuyor.
- **Repair Schema Fix**: `repair_jobs` tablosundaki eksik `meta` sütunu Alembic `0008` migrasyonu ile eklendi.
- **Lifespan Task**: `startup/lifespan.py` içerisinde otonom onarım sisteminin açılışta otomatik "warmup" (ısınma) yapması sağlandı.
- **Verification**: Hydration ve persistence süreçleri persistent DB testleriyle %100 doğrulandı.
- **Task**: [repair_orchestrator.py](file:///e:/ai_company_faz12.1/core/repair_orchestrator.py), [lifespan.py](file:///e:/ai_company_faz12.1/startup/lifespan.py) güncellendi.

### Yeni Test Dosyaları (RC1.1)
| Dosya | Testler |
|---|---|
| `tmp_verify_hydration.py` (Doğrulandı) | 5 test — hydration |
| `tmp_test_job.py` (Doğrulandı) | 3 test — job persistence |

### RC1.1 Kabul Kriterleri Durumu
| Kriter | Durum |
|---|---|
| Restart sonrası olaylar dashboard'da görünüyor | ✅ |
| Onarım görevleri (Apply) DB'ye hatasız yazılıyor | ✅ |
| Alembic migrasyonu (0008) uygulandı | ✅ |
| Model fallback (429 handling) stabil çalışıyor | ✅ |

### Phase 18 — Metacognitive Policy Evolution (Faz 12.1 Evolution)
- **Metacognitive Layer**: `PolicyEvolutionEngine` ve `GoalSynthesizer` ile sistemin kendi kurallarını ve stratejik hedeflerini otonom olarak iyileştirmesi sağlandı.
- **Dynamic Policy Engine**: `PolicyEngine` artık JSON tabanlı dinamik eşikler (`thresholds`) ve `AutomationLevel` (PR bazlı otonomi) ile çalışıyor.
- **Hierarchical Cognition**: `NexusOrchestrator` ve `NeuralCoreOrchestrator` ile hiyerarşik zihinsel işleme modeline geçildi.
- **Motor Subsystem & Execution**: `MotorSubsystem`, `QuantumExecutor` ve `EvolutionaryArchitect` ile operasyonel çekirdek sertleştirildi.
- **AuditGate Hardening**: Gelişen risk eşikleri ve politika motoruyla tam uyumlu, otonom onayı yöneten güvenlik katmanı (`AuditGate`) güncellendi.
- **Verification**: `verify_phase_18.py` ile tüm bilişsel nodların (Policy, Goal, Audit) stabil olduğu doğrulandı.
