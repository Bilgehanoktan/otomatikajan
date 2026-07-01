# Refine Control Plane Sayfa Bazlı Test Planı

Bu doküman `apps/refine_control_plane/src/app` altındaki route yüzeyleri için sayfa bazlı QA ve E2E test planıdır. Son canlı audit kaynağı `runtime/live-test/page-audit-results.json` temel alınarak hazırlanmıştır.

## Kapsam ve Baseline

- Toplam route: `81`
- Son canlı audit sonucu: `79 ok`, `2 skipped_no_sample`
- `skipped_no_sample` route'lar: `/governor/alerts/[id]`, `/project-factory/[project_id]`
- Hedef local yüzeyler: `cms` (`http://127.0.0.1:3100`), `app` (`http://127.0.0.1:8000`), `bilgeapi` (`http://127.0.0.1:8100`), `telegram-bot`
- Standart tekrar audit komutu:

```powershell
C:\Python314\python.exe -c "import runpy; runpy.run_path(r'runtime/live-test/page_audit.py', run_name='__main__')"
```

## Genel Kabul Kriterleri

Her sayfa için aşağıdaki kontroller ortak kabul kriteridir:

- Sayfa `HTTP 200` ile açılmalı; auth gerekiyorsa login akışı stabil çalışmalı.
- `page_error`, `console.error`, hydration hatası ve `Unhandled Runtime Error` olmamalı.
- Ana layout, sidebar, header, breadcrumb veya sayfa başlığı tutarlı görünmeli.
- Sayfa yüklenirken loading state; veri yokken empty state; hata alındığında error/retry state test edilmeli.
- API çağrıları doğru endpoint, method ve status kodlarıyla tamamlanmalı.
- Yetki gerektiren aksiyonlarda read-only rol, admin rol ve forbidden state ayrıca test edilmeli.
- Destructive veya state değiştiren butonlar için onay, sonuç bildirimi, audit kaydı ve rollback/refresh davranışı kontrol edilmeli.

---

## Sayfa Bazlı Plan

### 1. `/`

**Ne işe yarar:** Ana operasyon panelidir; sistem durumu, iş akışlarına hızlı geçiş, runtime sinyalleri ve yönetim modülleri için ilk kontrol yüzeyidir.
**Nereleri tetikler:** CMS shell, dashboard veri kartları, health/runtime özetleri, navigation route'ları ve ilgili API proxy katmanı.
**Örnek testler:** Sayfayı login sonrası aç ve ana kartların göründüğünü doğrula; her hızlı geçiş linkinin hedef route'a gittiğini kontrol et; dashboard API'lerinden biri hata döndürürse error veya retry state'in layout'u bozmadığını test et; console ve network hatası olmadığını Playwright ile kaydet.

### 2. `/approvals`

**Ne işe yarar:** Onay bekleyen governance işlerini ve operatör karar kuyruğunu listeler.
**Nereleri tetikler:** `/api/v1/governance/approvals` listeleme, karar/patch aksiyonları, filtreleme ve detay sayfasına geçiş.
**Örnek testler:** Liste dolu, boş ve hata durumlarını test et; bir kaydın detay linkinin `/approvals/[id]` route'una gittiğini doğrula; approve/reject benzeri butonların doğru method ve payload ile çalıştığını intercept et; read-only kullanıcıda karar butonlarının devre dışı kaldığını kontrol et.

### 3. `/approvals/[id]`

**Ne işe yarar:** Tek bir approval kaydının kanıtlarını, risk bilgisini ve karar aksiyonlarını gösterir.
**Nereleri tetikler:** Approval detail fetch, `POST /api/v1/governance/approvals/{id}/decide`, audit trail yenileme ve sonuç bildirimi.
**Örnek testler:** Geçerli sample id ile başlık, durum ve kanıt alanlarını doğrula; approve/reject kararı sonrası status badge ve toast sonucunu kontrol et; geçersiz id için 404-safe veya not-found state test et; karar sonrası sayfa refresh edildiğinde yeni durumun korunduğunu doğrula.

### 4. `/audit`

**Ne işe yarar:** Sistem audit ve kanıt izlerini operatöre genel bakış olarak sunar.
**Nereleri tetikler:** Audit/proof kayıt listeleri, timeline kartları, filtreler ve governance kanıt linkleri.
**Örnek testler:** Audit timeline'ın sıralı geldiğini kontrol et; tarih/severity filtreleri varsa uygulandığında liste ve URL state'inin tutarlı kaldığını doğrula; boş audit listesinde anlamlı empty state bekle; backend hata döndürdüğünde retry butonu ve console temizliğini test et.

### 5. `/axiology`

**Ne işe yarar:** Sistem değerleri, ilke setleri ve axiology kayıtlarının genel görünümüdür.
**Nereleri tetikler:** Axiology liste kartları, detay linkleri, statik veya API destekli ilke verileri.
**Örnek testler:** İlke kartlarının başlık ve açıklama ile render edildiğini doğrula; her karttan `/axiology/[id]` detayına gidiş test et; veri boş geldiğinde empty state gör; mobil viewport'ta kart grid'inin taşma yapmadığını screenshot ile doğrula.

### 6. `/axiology/[id]`

**Ne işe yarar:** Tek bir axiology ilkesinin detay, bağlam ve ilgili governance referanslarını gösterir.
**Nereleri tetikler:** Axiology detail resolver, geri dönüş linkleri, ilgili proof/governance bağlantıları.
**Örnek testler:** Geçerli sample id ile detay başlığı, metin ve referanslarin göründüğünü kontrol et; geçersiz id için not-found state test et; geri dönüş butonunun `/axiology` route'una döndüğünü doğrula; uzun metinlerde layout taşmasını mobil ve desktop'ta kontrol et.

### 7. `/bilgeapi-ops`

**Ne işe yarar:** BilgeAPI operasyon panelidir; runtime, watchdog, release, review ledger ve servis sağlığı yönetilir.
**Nereleri tetikler:** BilgeAPI health, catalog, watchdog, release/system action endpoint'leri, servis restart veya review aksiyonları.
**Örnek testler:** Health kartlarının `app` ve `bilgeapi` durumunu doğru yansıttığını kontrol et; destructive olmayan refresh/review aksiyonlarını tetikle ve API status'unu doğrula; servis hata senaryosunda panelin okunabilir error state verdiğini test et; operasyon butonlarında yetki ve confirmation davranışını kontrol et.

### 8. `/calibrations`

**Ne işe yarar:** Governor kalibrasyon önerilerini ve kabul/red kararlarını yönetir.
**Nereleri tetikler:** Calibration proposal listesi, propose/approve/reject benzeri state değiştiren endpoint'ler ve governance audit kaydı.
**Örnek testler:** Mevcut calibration kartlarını ve status badge'lerini doğrula; yeni proposal formu varsa validasyonları test et; approve/reject aksiyonunda network payload, toast ve list refresh sonucunu kontrol et; aynı aksiyonu tekrar çalıştırınca idempotent veya beklenen hata state'ini doğrula.

### 9. `/compliance`

**Ne işe yarar:** Compliance durumunu, kontrol listelerini ve audit bundle üretimini merkezi olarak gösterir.
**Nereleri tetikler:** `/api/v1/governance/compliance/audit-bundles`, compliance summary, bundle oluşturma ve detay linkleri.
**Örnek testler:** Mevcut uyum durum kartlarını kontrol et; yeni audit bundle indirme aksiyonlarının API isteklerini doğrula; hata durumunda retry akışını denetle.

### 10. `/compliance/audit-bundles`
**Ne işe yarar:** Uyum (compliance) denetim paketlerini listeler ve yeni paket indirme/oluşturma yeteneği sunar.
**Nereleri tetikler:** `GET /api/v1/governance/compliance/audit-bundles`, bundle indirme API proxy'si.
**Örnek testler:** Sayfayı açıp mevcut bundle listesini doğrula; yeni bundle oluşturma aksiyonunun API isteğini doğru payload ile gönderdiğini denetle; boş listede empty state gösterimini test et.

### 11. `/costs`
**Ne işe yarar:** Ajanların API kullanım maliyetlerini, harcanan token miktarlarını ve bütçe sınırlarını grafik ve tablolarla gösterir.
**Nereleri tetikler:** `/api/v1/costs/summary`, maliyet limit güncelleme API'leri.
**Örnek testler:** Sayfayı açıp grafiklerin doğru yüklenip yüklenmediğini Playwright ile kontrol et; kota aşımı uyarı badge'lerini test et; limit güncelleme formundaki input validasyonlarını doğrula.

### 12. `/evolution`
**Ne işe yarar:** Ajan davranış modellerinin ve sistem kurallarının zaman içindeki değişim ve evrim tarihçesini gösterir.
**Nereleri tetikler:** `/api/v1/evolution/history`.
**Örnek testler:** Evrim adımlarını listeleyen timeline bileşenini doğrula; arama ve filtreleme kutularının çalışmasını test et; detay kartlarındaki json fark (diff) görünümünü kontrol et.

### 13. `/federation` & `/federation/conflicts`
**Ne işe yarar:** Birden fazla AGI düğümü veya repozitory arasındaki senkronizasyonu ve çakışma (conflict) durumlarını yönetir.
**Nereleri tetikler:** `/api/v1/federation/topology`, senkronizasyon tetikleme ve çakışma çözümleme endpoint'leri.
**Örnek testler:** Topoloji şemasının doğru render edildiğini kontrol et; çakışma çözümleme aksiyonunun doğru API çağrısını yaptığını test et; çakışma yokken temiz durum ekranını doğrula.

### 14. `/fleet` & `/fleet/agents` & `/fleet/operations`
**Ne işe yarar:** Sistemde aktif çalışan otonom ajan filolarını, rollerini, anlık durumlarını ve yürüttükleri operasyonları listeler.
**Nereleri tetikler:** `/api/v1/fleet/containers` ve ajan kontrol API'leri.
**Örnek testler:** Aktif ajan sayısını ve statülerini doğrula; ajan durdurma/başlatma aksiyonlarında onay (confirmation) kutusunu ve API sonuçlarını test et.

### 15. `/governance/...` (Yönetişim Alt Sayfaları)
**Ne işe yarar:** `/governance/approvals`, `/governance/audit`, `/governance/compliance` gibi ana yönetişim yollarının refine-routing ile doğrudan erişilen yansımalarıdır.
**Nereleri tetikler:** İlgili `/api/v1/governance/*` endpoint'leri.
**Örnek testler:** Doğrudan URL ile erişimi doğrula; alt sekmelerin (tabs) geçiş hızını ve hydration durumlarını test et.

### 16. `/governor/...` (Özerklik ve Denetim Alt Sayfaları)
**Ne işe yarar:** Özerklik kapısı, politika sapmaları (drifts), acil durum senaryoları (drills) ve kanıt kontrol mekanizmalarını yönetir.
**Nereleri tetikler:** `/api/v1/governor/*` endpoint'leri.
**Örnek testler:** `Lock Autonomy Gate` ve `Unlock Autonomy Gate` butonlarının tetiklediği aksiyonları ve onay mekanizmasını test et; sapma (drift) grafiklerini doğrula.

### 17. `/identity`
**Ne işe yarar:** Ajan ve operatör kimlik doğrulama, API anahtarı yönetimi ve yetki tanımlarını gösterir.
**Nereleri tetikler:** `/api/v1/system/management-gate`.
**Örnek testler:** API key oluşturma ve silme akışlarını doğrula; key maskeleme ve kopyalama butonlarının çalışmasını test et.

### 18. `/improvements`
**Ne işe yarar:** Sistem verimliliğini, kod kalitesini ve hızını artırmak için tespit edilen iyileştirme fırsatlarını (opportunities) listeler.
**Nereleri tetikler:** `/api/v1/improvements/opportunities`.
**Örnek testler:** İyileştirme kartlarındaki puanlama ve öncelik sıralamalarını kontrol et; bir iyileştirmeyi onaylayıp onarım kuyruğuna aktarma butonunu test et.

### 19. `/incidents` & `/governance/incidents`
**Ne işe yarar:** Güvenlik ve kural ihlallerine dair oluşan tüm olayları (incidents) listeler.
**Nereleri tetikler:** `/api/v1/governance/incidents` ve detay API'leri.
**Örnek testler:** Olayların severity derecelerine göre doğru renklendirildiğini kontrol et; detay sayfasına geçişi ve çözüm/kapatma aksiyonlarını test et.

### 20. `/learning/...` (Öğrenme ve Strateji Belleği)
**Ne işe yarar:** Ajanların geçmiş deneyimlerden çıkardığı negatif desenleri (negative-patterns), adaptasyon önerilerini ve strateji belleklerini listeler.
**Nereleri tetikler:** `/api/v1/learning/*` endpoint'leri.
**Örnek testler:** Strateji kartlarının doğru render edildiğini doğrula; negatif desen detayını inceleme akışını test et.

### 21. `/login`
**Ne işe yarar:** Operatörlerin sisteme güvenli kimlik doğrulaması ile girmesini sağlar.
**Nereleri tetikler:** `POST /api/v1/auth/login`.
**Örnek testler:** Yanlış şifre ile hata mesajını kontrol et; başarılı girişte yönlendirme akışını Playwright ile doğrula.

### 22. `/mcp-hub`
**Ne işe yarar:** Model Context Protocol (MCP) sunucularını listeler, aktiflik durumlarını gösterir ve yeni araç ekleme yeteneği sunar.
**Nereleri tetikler:** MCP sunucu yönetim API'leri.
**Örnek testler:** Bağlı sunucuların listesini doğrula; yeni sunucu tanımlama formundaki validasyonları test et.

### 23. `/meeting-room`
**Ne işe yarar:** Ajanlar arasında karmaşık kararlar için yapılan otonom tartışmaları ve konsensüs (quorum) süreçlerini görselleştirir.
**Nereleri tetikler:** `/api/v1/debate/sessions`.
**Örnek testler:** Tartışma ağacını (dialogue tree) kontrol et; karara bağlanan oturumların durum badge'lerini doğrula.

### 24. `/mesh`
**Ne işe yarar:** Güvenlik ve uyum doğrulamalarını gerçekleştiren doğrulayıcı ağının (verifier mesh) durumunu gösterir.
**Nereleri tetikler:** `/api/v1/mesh/rules`.
**Örnek testler:** Aktif kuralları doğrula; kural aktifleştirme/pasifleştirme switch butonlarının çalışmasını test et.

### 25. `/ops/handover-status` & `/ops/launch-gates`
**Ne işe yarar:** Geliştirilen özelliklerin veya yapılan onarımların üretim ortamına geçiş onay durumlarını gösterir.
**Nereleri tetikler:** Launch gates ve signoff durum endpoint'leri.
**Örnek testler:** Kapı durumlarının (passed/failed) doğru badge'lerle gösterildiğini kontrol et; manuel imza/onay butonlarını test et.

### 26. `/policy-proposals`
**Ne işe yarar:** Sistem kuralları ve güvenlik sınırlarını belirleyen politika tekliflerini operatör onayına sunar.
**Nereleri tetikler:** Politika oluşturma ve oylama API'leri.
**Örnek testler:** Yeni politika ekleme formunu test et; oylama butonlarının payload doğruluğunu denetle.

### 27. `/project-factory` & `/project-factory/[project_id]`
**Ne işe yarar:** AGI tarafından oluşturulan alt projeleri ve bunların portföy durumlarını yönetir.
**Nereleri tetikler:** `/api/v1/project-factory/projects`.
**Örnek testler:** Arama ve filtreleme kutularının çalışmasını test et; yeni proje oluşturma sihirbazını doğrula.

### 28. `/prompt-studio`
**Ne işe yarar:** Ajan sistem prompt'larının test edildiği, versiyonlandığı ve yönetildiği stüdyodur.
**Nereleri tetikler:** `/api/v1/prompt-studio/prompts`.
**Örnek testler:** Prompt editörünün doğru render edildiğini kontrol et; prompt kaydetme ve geri alma aksiyonlarını doğrula.

### 29. `/proof/events` & `/proof/snapshots`
**Ne işe yarar:** Otonom işlemlerin kanıt zincirlerini (provenance) ve kriptografik anlık kanıt görüntülerini listeler.
**Nereleri tetikler:** `/api/v1/proof/artifacts`.
**Örnek testler:** Kanıt listesinin doğru yüklendiğini kontrol et; kanıt detayı görüntüleme butonlarını test et.

### 30. `/repair-lab` & `/repair-lab/improvements`
**Ne işe yarar:** Arayüz ve kod onarım süreçlerinin simüle edildiği, test edildiği laboratuvar arayüzüdür.
**Nereleri tetikler:** `/api/v1/repair-lab/ui-runs` ve `/api/v1/repair-lab/self-repair-runs`.
**Örnek testler:** Onarım döngüsü tetikleme butonlarını test et; çalışma durumunu gösteren spinner ve progress bar bileşenlerini doğrula.

### 31. `/repair-memory`
**Ne işe yarar:** Geçmişte başarıyla tamamlanmış onarımların yamalarını (patches) ve kalıcı öğrenme belleklerini listeler.
**Nereleri tetikler:** `/api/v1/repair-memory/patches`.
**Örnek testler:** Yama listesindeki diff görünümünü doğrula; yama arama kutusunun performansını test et.

### 32. `/safety`
**Ne işe yarar:** Çalışma zamanı (sandbox) güvenlik kısıtlamalarını ve güvenlik duvarı ayarlarını operatöre sunar.
**Nereleri tetikler:** `/api/v1/safety/sandbox-config`.
**Örnek testler:** Kısıtlı dizinler listesini doğrula; güvenlik modu değiştirme aksiyonlarının uyarı pencerelerini test et.

### 33. `/self-tuning` & `/self-tuning/scoped`
**Ne işe yarar:** Ajan parametrelerinin, sıcaklık (temperature) ve token limitlerinin sistem tarafından kendi kendine ayarlanma günlüklerini (tuning logs) gösterir.
**Nereleri tetikler:** `/api/v1/self-tuning/logs`.
**Örnek testler:** Günlük listesinin doğru yüklendiğini kontrol et; filtrelerin çalışma durumunu test et.

### 34. `/system-health`
**Ne işe yarar:** Disk, CPU, RAM, veritabanı bağlantısı ve Docker konteyner sağlık durumlarını gösterir.
**Nereleri tetikler:** `/health` ve `/v1/system/profile`.
**Örnek testler:** Bileşen sağlık grafiklerinin doğru yüklendiğini doğrula; uyuşmazlık durumunda alarm tetikleme mekanizmasını test et.

### 35. `/training`
**Ne işe yarar:** Lokal ince ayar (fine-tuning) veya kural eğitimlerinin çalıştırılma durumlarını gösterir.
**Nereleri tetikler:** `/api/v1/training/runs`.
**Örnek testler:** Eğitim kuyruğu listesini doğrula; yeni eğitim başlatma aksiyonunu test et.

### 36. `/ui-repair`
**Ne işe yarar:** Otonom arayüz onarım döngülerine genel bakış sağlar.
**Nereleri tetikler:** Arayüz onarım tetikleyicileri.
**Örnek testler:** Hata tespit grafiğini doğrula; onarım başlatma butonlarının yetki kontrollerini test et.

### 37. `/verifiers`
**Ne işe yarar:** Sistemdeki tüm doğrulama kurallarını ve parametrelerini listeler.
**Nereleri tetikler:** `/api/v1/verifiers/rules`.
**Örnek testler:** Kural kartlarının listelenmesini doğrula; kural detayı modal pencerelerini test et.

### 38. `/workflows` & `/workflows/[id]` & `/workflows/create`
**Ne işe yarar:** Ajanların yürüttüğü çok adımlı bilişsel iş akışlarını listeler, oluşturur ve izler.
**Nereleri tetikler:** `/api/v1/workflows/stats/summary` ve detay endpoint'leri.
**Örnek testler:** Akış şeması görselleştirmelerini doğrula; yeni iş akışı oluşturma formunu test et.

---

## 🛠️ Skipped Route'lar İçin Aksiyon Planı

Canlı testlerde veri bulunamadığı için atlanan (`skipped_no_sample`) aşağıdaki route'lar için test verisi hazırlama adımları:

1. **/governor/alerts/[id]**:
   - Testten önce sisteme sahte bir governor uyarısı tetikleyin:
     ```bash
     curl -X POST http://127.0.0.1:8100/v1/governor/alerts/simulate -d '{"type": "drift_detected"}'
     ```
2. **/project-factory/[project_id]**:
   - Portföy aramalarında veri çıkması için API üzerinden yeni bir test projesi başlatın:
     ```bash
     curl -X POST http://127.0.0.1:8100/v1/project-factory/projects -d '{"name": "E2E Test Projesi"}'
     ```
