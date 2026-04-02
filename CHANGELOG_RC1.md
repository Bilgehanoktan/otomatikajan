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

### Sprint 7 — Model Resilience & Gateway Integration (Faz 12.12.x)
- **OpenRouter Integration**: OpenRouter API ağ geçidi (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`) entegre edildi. Sistem artık Anthropic modellerine OpenRouter üzerinden öncelikli erişim sağlıyor.
- **llm/model_orchestrator.py**: Model yönlendirme politikaları OpenRouter sağlayıcısını destekleyecek şekilde güncellendi; 429 ve 400 hataları için otonom fallback mekanizması güçlendirildi.
- **.env**: `OPENROUTER_API_KEY` ve sağlayıcı spesifik konfigürasyonlar eklendi.

### Sprint 8 — Sovereign State Reliability & Governance Hardening
- **Database Schema (subtasks)**: `subtasks` tablosuna `internal_monologue` sütunu eklendi. Bu sayede otonom ajanların içsel akıl yürütme süreçleri kalıcı hale getirildi ve bilişsel şeffaflık sağlandı.
- **Core/Governance**: `GovernanceWatchdog` ve `SelfAuditAgent` aktif edildi. Sistem artık mimari ihlalleri otonom olarak tespit edip raporlayabiliyor.
- **Kinetic Resilience**: `SovereignCortex` üzerinde otonom kaynak arbitrasyonu ve hata kurtarma döngüleri (Recovery Loops) sertleştirildi.
- **Verification**: `verify_phase_42-49.py` serisi ile egemen yönetişim ve hafıza sürekliliği doğrulandı.

### Sprint 9 — Recursive Strategic Depth & Metabolic Governance (Faz 13.0)
- **Sovereign Depth**: `SovereignPlanner` ve `SovereignCortex` rekürsif planlama (Phase 51) desteğiyle güncellendi. Artık karmaşık hedefler otonom olarak alt-planlara bölünüp derinlemesine çözülebiliyor.
- **Metabolic Governance**: `MetabolicGovernor` (Phase 52) entegre edildi. Sistem artık LLM sağlayıcılarının anlık gecikme ve hata oranlarını izliyor, rotalamayı otonom olarak (metabolik sağlığa göre) optimize ediyor.
- **Task Governance**: `GovernedTask` şemasına hiyerarşik yapı (`parent_id`, `is_complex`) alanları eklendi.
- **Verification**: `test_recursive_depth_v51.py` ve `test_metabolic_surge_v52.py` ile hiyerarşik planlama ve otonom kaynak adaptasyonu doğrulandı.

### Sprint 10 — Ethics, Persistence & Sovereign Mastery (Faz 12.1 v121.0)
- **Phase 50: Sovereign Grounding**: `AgiGoalDecomposer` refaktör edildi. Ajanların araç kullanımı (tooling) ve dosya sistemi bağlamı üzerindeki farkındalıkları (grounding) derinleştirildi.
- **Phase 53: Positive Learning**: Başarı ve hata analizlerinden beslenen otonom ajan kontratı iyileştirme döngüsü aktif edildi. Sistem artık "tecrübe" kazanabiliyor.
- **Phase 54: Sovereign Code Generation**: Kod üretimi mimarisi `sovereign_codegen` ile persistent (DB-backed) hale getirildi. Üretilen yamaların izlenebilirliği ve geri kurtarılabilirliği sağlandı.
- **Phase 55: Ethical Guardrails**: `AxiologyEngine` otonom bir hakem (arbiter) olarak yapılandırıldı. Tüm görevler için zorunlu etik denetim ve risk analizi katmanı eklendi.
- **Verification**: `test_sovereign_grounding_v50.py`, `test_positive_learning_v53.py`, `test_codegen_db_logic_v2.py` ve `test_ethical_guardrails_v55.py` ile v121.0 bütünlüğü doğrulandı.

### Sprint 11 � Stabilization & Cognitive Repair (Faz 12.1 Internal)
- **db/session.py**: Oturum y�netimi g��lendirildi. IntegrityError ve PendingRollbackError an�nda otomatik temizlik ve ba�lant� kurtarma (Session Hardening) eklendi.
- **core/agi/cognitive/metacognitive_auditor.py**: Idempotent UPSERT mant���na ge�ildi. M�kerrer kay�tlar art�k hata f�rlatmak yerine mevcut kayd� g�ncelliyor (Race Condition Protection).
- **core/heal_engine.py**: Sistem geneli sa�l�k metrikleri (Error Rate, DB Connectivity) takip edilmeye ba�land�. Sa�l�k skoru hesaplamas� sistemik hatalar� i�erecek �ekilde g�ncellendi.
- **Verification**: verify_upsert.py ve verify_heal_engine.py ile y�ksek hata tolerans� ve stabilite do�ruland�.


### Sprint 12 - CEO Engine Strategic Observability & Persistence (Faz 12.1 Final)
- **core/ceo_engine.py**: `run_scan()` içerisindeki kritik `NameError` (uninitialized `opportunities`) giderildi.
- **Persistence Hardening**: `CEOEngine` tarafında stratejik bulguların ve önerilen görevlerin DB'ye kalıcı olarak yazılması için `db.commit()` mekanizması entegre edildi.
- **Startup Stability**: `metacognitive_auditor.py` içerisindeki eksik `AgentOutput` importu giderilerek server çökmesi (startup crash) engellendi.
- **Verification**: `scripts/test_ceo_persistence.py` ile veritabanı yazma süreçleri ve otonom tarama bütünlüğü host ve container üzerinde %100 doğrulandı.
- **Dashboard Sync**: CEO Denetimi sayfası, terminal-inspired manifesto ve canlı senkronize edilen 1000+ bulgu ile v121.0 standartlarına yükseltildi.
