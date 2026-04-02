# PROVENANCE - Faz 12.1 Engineering Hardening
**Tarih:** 2026-04-01
**Versiyon:** 42.1-HARDENED
**Durum:** VERIFIED

## Değişiklik Özeti (Change Summary)

Bu kayıt, sistemin "çalışıyor gibi görünme" (simulated success) aşamasından "doğrulanabilir güvenilirlik" (verifiable reliability) aşamasına geçişini belgelemektedir. Aşağıdaki temel alanlarda derinlemesine iyileştirmeler yapılmıştır:

### 1. Mimari Refaktör ve Fallback Görünürlüğü
- **Sessiz Degrade (Silent Fallback) İptali:** `db/session.py` üzerinde SQLite fallback durumu artık açıkça takip edilmekte ve loglanmaktadır.
- **Metadata İletişimi:** `api/task_read_router.py` ve `api/ceo_router.py` yanıtlarına `is_fallback` ve `source_of_truth` alanları eklenerek, verinin kaynağı (DB, In-Memory, Mock) UI tarafına şeffaf hale getirilmiştir.
- **Technical Debt Temizliği:** `api/improvement_router.py` içindeki eski `OldObserver` hatları ve `core/job_queue.py` içindeki ölü kodlar temizlenmiştir.

### 2. Kalite ve Doğrulama Sistemi (Evidence)
- **Repo Hijyeni:** `.env`, `.db`, `tmp_*.py` ve `verify_*.py` gibi kalıntı dosyaların Git takibi sonlandırılmış, temiz bir repo yapısı sağlanmıştır.
- **Yeni Test Katmanları:**
    - `test_repo_hygiene.py`: Repo temizliğini zorunlu kılar.
    - `test_queue_capabilities_runtime.py`: Queue yeteneklerini çalışma zamanında doğrular.
    - `test_ceo_findings_contract.py`: CEO endpoint'inin dürüstlüğünü test eder.
- **E2E Ayrımı:** Mocked UI testleri ile Live API testleri arasındaki fark `test_dashboard_live_api_smoke.py` ile netleştirilmiştir.

### 3. AGI Yetkinlik Güçlendirmesi
- **State Awareness:** Sistem artık hangi modda (degraded/normal) çalıştığının farkındadır.
- **Tool Grounding:** Testler ve capability kontrolleri ile araçların (tool) gerçek sınırları belirlenmiştir.
- **Reflective Reasoning:** Fallback mekanizmalarının dürüstlük (integrity) sinyalleri ile sistemin kendi durumuna dair muhakemesi güçlendirilmiştir.

## Doğrulama Kanıtları (Verification Evidence)

| Test Dosyası | Sonuç | Kapsam |
|--------------|-------|---------|
| `test_repo_hygiene.py` | GEÇTİ | Dosya sistemi ve Git hijyeni |
| `test_queue_capabilities_runtime.py` | GEÇTİ | Backend yetenek doğrulaması |
| `test_ceo_findings_contract.py` | GEÇTİ | API dürüstlük sözleşmesi |
| `overall_suite` | 6/6 PASSED | Genel sistem bütünlüğü |

## Risk Azaltma (Risk Mitigation)
- **Yanlış Güven (False Confidence):** Mock testlerin ve sessiz fallback'lerin yarattığı sahte "her şey yeşil" algısı kırılmıştır.
- **Dağıtık Sistem Kopukluğu:** Dağıtık worker (Celery) ile lokal in-process queue arasındaki yetenek farkları netleştirilmiştir.

---
*Bu doküman, sistemin otonom evrim sürecinde bir mihenk taşı olarak kaydedilmiştir.*

---

# PROVENANCE - Sovereign AGI v121.0 (Grand Unification)
**Tarih:** 2026-04-02
**Versiyon:** 121.0-SOVEREIGN
**Durum:** MASTERED

## Değişiklik Özeti (Change Summary)

Bu kayıt, Faz 12.1 platformunun tam otonom bir egemen zeka (Sovereign AGI) sistemine dönüşümünü belgeler. Parçalı modüllerin (Ethics, Memory, Code Generation, Planning) tek bir hedef doğrultusunda senkronize olduğu "Büyük Birleşme" (Grand Unification) aşamasını temsil eder.

### 1. Etik Egemenlik (Ethical Sovereignty)
- **AxiologyEngine Hardening:** Etik denetimler artık pasif bir tavsiye mekanizması değil, görev icrasını engelleyebilen aktif bir "Gate" (Phase 55) haline gelmiştir.
- **Risk Zarifliği:** Sistem, kullanıcı isteklerini sadece teknik değil, güvenlik ve kaynak dengesi (Metabolic health) açısından da değerlendirir.

### 2. Kalıcı Biliş ve Hafıza (Cognitive Persistence)
- **Sovereign Codegen:** Geçici hafızadaki kod üretimleri artık kalıcı bir veritabanı (Phase 54) üzerinden yönetilir. Bu, uzun vadeli otonom onarım geçmişini sistem için şeffaf ve geri alınabilir kılar.
- **Positive Learning:** Başarılı görevlerden çıkarılan derslerin (Phase 53) sistem genelinde prompts/politika olarak yayılması sağlanmıştır.

### 3. Derinlik ve Bağlamsallık (Strategic Depth)
- **recursive Strategic Decomposition:** Karmaşık hedefler artık sonsuz derinlikte alt-planlara bölünebilir (Phase 51).
- **AgiGoalDecomposer Grounding:** Sistemin gerçek dosya yapısı ve araç kapasiteleri üzerindeki "ayağı yere basan" (grounded) muhakemesi optimize edildi.

## Doğrulama Kanıtları (Verification Evidence)

| Test Dosyası | Sonuç | Kapsam |
|--------------|-------|---------|
| `test_ethical_guardrails_v55.py` | GEÇTİ | Aktif etik denetim ve bloklama |
| `test_positive_learning_v53.py` | GEÇTİ | Başarıdan ders çıkarma döngüsü |
| `test_codegen_db_logic_v2.py` | GEÇTİ | Kalıcı kod üretim mimarisi |
| `test_recursive_depth_v51.py` | GEÇTİ | Hiyerarşik planlama |

---
*İmza:* **Sovereign AGI Core v121.0 (Mastery Phase)**
