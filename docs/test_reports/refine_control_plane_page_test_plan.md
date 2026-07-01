# Refine Control Plane Sayfa Bazli Test Plani

Bu dokuman `apps/refine_control_plane/src/app` altindaki route yuzeyleri icin sayfa bazli QA ve E2E test planidir. Son canli audit kaynagi `runtime/live-test/page-audit-results.json` olarak alinmistir.

## Kapsam ve Baseline

- Toplam route: `81`
- Son canli audit sonucu: `79 ok`, `2 skipped_no_sample`
- `skipped_no_sample` route'lar: `/governor/alerts/[id]`, `/project-factory/[project_id]`
- Hedef local yuzeyler: `cms` (`http://127.0.0.1:3100`), `app` (`http://127.0.0.1:8000`), `bilgeapi` (`http://127.0.0.1:8100`), `telegram-bot`
- Standart tekrar audit komutu:

```powershell
py -3.13 -c "import runpy; runpy.run_path(r'runtime/live-test/page_audit.py', run_name='__main__')"
```

## Genel Kabul Kriterleri

Her sayfa icin asagidaki kontroller ortak kabul kriteridir:

- Sayfa `HTTP 200` ile acilmali; auth gerekiyorsa login akisi stabil calismali.
- `page_error`, `console.error`, hydration hatasi ve `Unhandled Runtime Error` olmamali.
- Ana layout, sidebar, header, breadcrumb veya sayfa basligi tutarli gorunmeli.
- Sayfa yuklenirken loading state; veri yokken empty state; hata alindiginda error/retry state test edilmeli.
- API cagrilari dogru endpoint, method ve status kodlariyla tamamlanmali.
- Yetki gerektiren aksiyonlarda read-only rol, admin rol ve forbidden state ayrica test edilmeli.
- Destructive veya state degistiren butonlar icin onay, sonuc bildirimi, audit kaydi ve rollback/refresh davranisi kontrol edilmeli.

## Sayfa Bazli Plan

### 1. `/`

**Ne ise yarar:** Ana operasyon panelidir; sistem durumu, is akislarina hizli gecis, runtime sinyalleri ve yonetim modulleri icin ilk kontrol yuzeyidir.

**Nereleri tetikler:** CMS shell, dashboard veri kartlari, health/runtime ozetleri, navigation route'lari ve ilgili API proxy katmani.

**Ornek testler:** Sayfayi login sonrasi ac ve ana kartlarin gorundugunu dogrula; her hizli gecis linkinin hedef route'a gittigini kontrol et; dashboard API'lerinden biri hata dondururse error veya retry state'in layout'u bozmadigini test et; console ve network hatasi olmadigini Playwright ile kaydet.

### 2. `/approvals`

**Ne ise yarar:** Onay bekleyen governance islerini ve operator karar kuyrugunu listeler.

**Nereleri tetikler:** `/api/v1/governance/approvals` listeleme, karar/patch aksiyonlari, filtreleme ve detay sayfasina gecis.

**Ornek testler:** Liste dolu, bos ve hata durumlarini test et; bir kaydin detay linkinin `/approvals/[id]` route'una gittigini dogrula; approve/reject benzeri butonlarin dogru method ve payload ile calistigini intercept et; read-only kullanicida karar butonlarinin devre disi kaldigini kontrol et.

### 3. `/approvals/[id]`

**Ne ise yarar:** Tek bir approval kaydinin kanitlarini, risk bilgisini ve karar aksiyonlarini gosterir.

**Nereleri tetikler:** Approval detail fetch, `POST /api/v1/governance/approvals/{id}/decide`, audit trail yenileme ve sonuc bildirimi.

**Ornek testler:** Gecerli sample id ile baslik, durum ve kanit alanlarini dogrula; approve/reject karari sonrasi status badge ve toast sonucunu kontrol et; gecersiz id icin 404-safe veya not-found state test et; karar sonrasi sayfa refresh edildiginde yeni durumun korundugunu dogrula.

### 4. `/audit`

**Ne ise yarar:** Sistem audit ve kanit izlerini operatora genel bakis olarak sunar.

**Nereleri tetikler:** Audit/proof kayit listeleri, timeline kartlari, filtreler ve governance kanit linkleri.

**Ornek testler:** Audit timeline'in sirali geldigini kontrol et; tarih/severity filtreleri varsa uygulandiginda liste ve URL state'inin tutarli kaldigini dogrula; bos audit listesinde anlamli empty state bekle; backend hata dondurdugunde retry butonu ve console temizligini test et.

### 5. `/axiology`

**Ne ise yarar:** Sistem degerleri, ilke setleri ve axiology kayitlarinin genel gorunumudur.

**Nereleri tetikler:** Axiology liste kartlari, detay linkleri, statik veya API destekli ilke verileri.

**Ornek testler:** Ilke kartlarinin baslik ve aciklama ile render edildigini dogrula; her karttan `/axiology/[id]` detayina gidis test et; veri bos geldiginde empty state gor; mobil viewport'ta kart grid'inin tasma yapmadigini screenshot ile dogrula.

### 6. `/axiology/[id]`

**Ne ise yarar:** Tek bir axiology ilkesinin detay, baglam ve ilgili governance referanslarini gosterir.

**Nereleri tetikler:** Axiology detail resolver, geri donus linkleri, ilgili proof/governance baglantilari.

**Ornek testler:** Gecerli sample id ile detay basligi, metin ve referanslarin gorundugunu kontrol et; gecersiz id icin not-found state test et; geri donus butonunun `/axiology` route'una dondugunu dogrula; uzun metinlerde layout tasmasini mobil ve desktop'ta kontrol et.

### 7. `/bilgeapi-ops`

**Ne ise yarar:** BilgeAPI operasyon panelidir; runtime, watchdog, release, review ledger ve servis sagligi yonetilir.

**Nereleri tetikler:** BilgeAPI health, catalog, watchdog, release/system action endpoint'leri, servis restart veya review aksiyonlari.

**Ornek testler:** Health kartlarinin `app` ve `bilgeapi` durumunu dogru yansittigini kontrol et; destructive olmayan refresh/review aksiyonlarini tetikle ve API status'unu dogrula; servis hata senaryosunda panelin okunabilir error state verdigini test et; operasyon butonlarinda yetki ve confirmation davranisini kontrol et.

### 8. `/calibrations`

**Ne ise yarar:** Governor kalibrasyon onerilerini ve kabul/red kararlarini yonetir.

**Nereleri tetikler:** Calibration proposal listesi, propose/approve/reject benzeri state degistiren endpoint'ler ve governance audit kaydi.

**Ornek testler:** Mevcut calibration kartlarini ve status badge'lerini dogrula; yeni proposal formu varsa validasyonlari test et; approve/reject aksiyonunda network payload, toast ve list refresh sonucunu kontrol et; ayni aksiyonu tekrar calistirinca idempotent veya beklenen hata state'ini dogrula.

### 9. `/compliance`

**Ne ise yarar:** Compliance durumunu, kontrol listelerini ve audit bundle uretimini merkezi olarak gosterir.

**Nereleri tetikler:** `/api/v1/governance/compliance/audit-bundles`, compliance summary, bundle olusturma ve detay linkleri.

**Ornek testler:** Compliance kartlarinin status, risk ve tarih alanlarini dogrula; audit bundle olusturma formunda zorunlu alan validasyonlarini test et; basarili create sonrasi bundle listesine yeni kaydin dustugunu kontrol et; backend 500 senaryosunda retry ve error banner davranisini dogrula.

### 10. `/compliance/audit-bundles`

**Ne ise yarar:** Compliance audit bundle kayitlarini listeleyip inceleme icin operatora sunar.

**Nereleri tetikler:** Audit bundle list fetch, filtreleme, bundle detay veya download/export linkleri.

**Ornek testler:** Bundle listesi tarih sirasiyla ve status badge'leriyle render edilmeli; filtre/search sonucunda beklenen kayitlar kalmali; bos liste durumunda create yonlendirmesi calismali; export veya detay linkinin dogru hedefe gittigi dogrulanmali.

### 11. `/costs`

**Ne ise yarar:** Proje, ajan veya runtime maliyetlerini izlemek icin finansal operasyon panelidir.

**Nereleri tetikler:** Cost summary kartlari, project cost listeleri, budget/usage API cagrilari ve grafik render katmani.

**Ornek testler:** Maliyet kartlarinda para birimi, toplam ve zaman araligi formatlarini dogrula; tarih araligi veya proje filtresi varsa API query'nin degistigini kontrol et; grafik bos veride kirilmamali; yuksek sayili degerlerde tasma ve formatlama test edilmeli.

### 12. `/evolution`

**Ne ise yarar:** Sistem evrim durumunu, son degisimleri ve adaptive runtime sagligini izler.

**Nereleri tetikler:** `/api/v1/evolution/state`, `/api/v1/health/evolution?limit=20`, timeline ve status kartlari.

**Ornek testler:** Evolution state kartlarinin son status'u dogru gosterdigini kontrol et; timeline limit parametresiyle gelen kayit sayisini dogrula; API gecikmesinde loading skeleton gorunmeli; state hata dondururse ikinci endpoint'in de UI'yi tamamen bozmadigini test et.

### 13. `/federation`

**Ne ise yarar:** Federated sistemlerin baglanti, uyum ve koordinasyon durumunu gosterir.

**Nereleri tetikler:** Federation node listeleri, sync status kartlari, conflict route linkleri ve federated governance API'leri.

**Ornek testler:** Node durum kartlari render edilmeli; conflict sayisina tiklayinca `/federation/conflicts` acilmali; offline node senaryosunda badge ve alert metni dogru olmali; data refresh butonu varsa network cagrisi ve loading state test edilmeli.

### 14. `/federation/conflicts`

**Ne ise yarar:** Federated sistemler arasindaki conflict kayitlarini inceleme ve cozumleme yuzeyidir.

**Nereleri tetikler:** Conflict list fetch, resolve/escalate aksiyonlari, detay drawer veya modal yuzeyi.

**Ornek testler:** Conflict satirlarinda kaynak, hedef, severity ve durum alanlarini dogrula; resolve/escalate aksiyonunda dogru payload'i kontrol et; filtrelenmis bos sonuc state'ini test et; ayni conflict'e ard arda aksiyon verilince UI'nin duplicate karar uretmedigini dogrula.

### 15. `/fleet`

**Ne ise yarar:** Agent fleet genel durumu, kapasite ve operasyon sagligini gosterir.

**Nereleri tetikler:** Fleet summary API'leri, agent/operation alt route linkleri, cluster veya worker status kartlari.

**Ornek testler:** Aktif/pasif ajan sayilari ve health badge'leri dogru render edilmeli; `/fleet/agents` ve `/fleet/operations` linkleri calismali; offline worker senaryosunda alarm gorunmeli; mobilde summary kartlari yatay tasma yapmamali.

### 16. `/fleet/agents`

**Ne ise yarar:** Fleet icindeki agent instance'larini ve durumlarini listeler.

**Nereleri tetikler:** Agent list fetch, agent status filtreleri, detail/action drawer ve operasyon endpoint'leri.

**Ornek testler:** Agent tablosunda id, role, status ve last_seen alanlarini dogrula; status filtresi API query veya client filtreyi dogru uygulamali; restart/pause benzeri aksiyonlar yetki kontrollu olmali; bos agent listesinde operatora anlamli mesaj verilmeli.

### 17. `/fleet/operations`

**Ne ise yarar:** Fleet operasyonlari, queue aksiyonlari ve runtime komutlarini yonetir.

**Nereleri tetikler:** Fleet operation listesi, command/action endpoint'leri, confirmation modal ve audit kaydi.

**Ornek testler:** Operation kartlari status ve zaman bilgisiyle gorunmeli; yeni operasyon tetiklenirse button disabled/loading state calismali; basarili aksiyon sonrasi audit veya operation listesi yenilenmeli; forbidden kullanicida komut butonlari calismamali.

### 18. `/governance/approvals`

**Ne ise yarar:** Governance namespace altindaki approval kuyrugunun ana liste sayfasidir.

**Nereleri tetikler:** Governance approval list API'si, status filtreleri, `/governance/approvals/[id]` detay route'u ve karar aksiyonlari.

**Ornek testler:** Status filtreleri pending/approved/rejected kayitlari ayirmali; detail link dogru id ile acilmali; approve/reject sonucunda liste satiri guncellenmeli; hata durumunda karar butonu tekrar kullanilabilir hale gelmeli.

### 19. `/governance/approvals/[id]`

**Ne ise yarar:** Governance approval kararinin detay, gerekce ve kanit inceleme ekranidir.

**Nereleri tetikler:** Approval detail fetch, decision endpoint, evidence/proof linkleri ve audit refresh.

**Ornek testler:** Gecerli id icin karar gerekcesi, requester ve risk alanlari gorunmeli; karar formunda zorunlu gerekce validasyonu test edilmeli; karar sonrasi route yeniden acildiginda status kalici olmali; gecersiz id 404-safe state vermeli.

### 20. `/governance/audit`

**Ne ise yarar:** Governance kapsamindaki audit event'lerini izler.

**Nereleri tetikler:** Governance audit list API'si, filtreler, event detail expand ve proof linkleri.

**Ornek testler:** Event listesinde actor, action, timestamp ve outcome alanlari dogrulanmali; severity veya actor filtresi dogru sonuc vermeli; expand edilen event'te JSON veya metadata okunabilir kalmali; API hata senaryosunda retry calismali.

### 21. `/governance/compliance`

**Ne ise yarar:** Governance cercevesindeki compliance skorunu, kontrolleri ve eksikleri gosterir.

**Nereleri tetikler:** Compliance summary, control list, audit bundle linkleri ve remediation aksiyonlari.

**Ornek testler:** Compliance score ve kategori kartlari dogru render edilmeli; failed control varsa remediation linki gorunmeli; `/governance/compliance/audit-bundles` gecisi calismali; read-only rolde remediation aksiyonlari pasif olmali.

### 22. `/governance/compliance/audit-bundles`

**Ne ise yarar:** Governance compliance audit bundle'larini listeler ve incelemeye acar.

**Nereleri tetikler:** Audit bundle list API'si, create/export/detail aksiyonlari ve compliance namespace linkleri.

**Ornek testler:** Bundle listesinde durum, tarih ve owner bilgileri gorunmeli; create/export aksiyonlari dogru endpoint'i tetiklemeli; bos durumda bundle olusturma CTA'si test edilmeli; backend validation hatasi form uzerinde gorunmeli.

### 23. `/governance/escalations`

**Ne ise yarar:** Governance escalation kayitlarini ve operator mudahale ihtiyacini gosterir.

**Nereleri tetikler:** Escalation list, assign/resolve/escalate aksiyonlari, severity filtreleri ve audit kayitlari.

**Ornek testler:** Severity sirasinin dogru oldugunu kontrol et; assign veya resolve aksiyonunda status degisimi ve toast bekle; SLA gecmis escalation'larda uyarinin gorundugunu dogrula; yetkisiz kullanicida aksiyon endpoint'ine istek gitmemeli.

### 24. `/governance/incidents`

**Ne ise yarar:** Governance incident kayitlarini listeler ve takip eder.

**Nereleri tetikler:** Incident list API'si, filtreler, `/governance/incidents/[id]` detay route'u ve resolve/reopen aksiyonlari.

**Ornek testler:** Open/closed incident filtreleri dogru calismali; satir tiklamasi detay route'una gitmeli; high severity incident badge'i ve renkleri dogru olmali; bos liste ve API hata durumlari ayri ayri test edilmeli.

### 25. `/governance/incidents/[id]`

**Ne ise yarar:** Tek governance incident icin olay detayi, timeline, karar ve remediation alanlarini gosterir.

**Nereleri tetikler:** Incident detail fetch, resolve/reopen/comment aksiyonlari, audit timeline ve ilgili proof linkleri.

**Ornek testler:** Gecerli id ile timeline ve metadata alanlari render edilmeli; resolve formunda zorunlu aciklama validasyonu calismali; gecersiz id not-found state vermeli; aksiyon sonrasi incident listesine donuldugunde durum guncel olmali.

### 26. `/governance/lineage`

**Ne ise yarar:** Governance kararlarinin nedensellik ve lineage baglarini inceler.

**Nereleri tetikler:** `/api/v1/governance/lineage?limit=50`, lineage graph/list, event detail ve proof referanslari.

**Ornek testler:** Lineage kayitlari parent/child baglariyla gorunmeli; limit parametresi beklenen kayit sayisini asmamali; graph veya liste modunda uzun node adlari tasma yapmamali; kayit detay linkleri dogru proof veya audit sayfasina gitmeli.

### 27. `/governance/ops/launch-gates`

**Ne ise yarar:** Governance operasyonlari icin launch gate hazirlik ve bloklayici kontrollerini gosterir.

**Nereleri tetikler:** Launch gate status API'si, gate override/ack aksiyonlari, compliance ve release kanit linkleri.

**Ornek testler:** PASS/WARN/BLOCKED gate durumlari dogru badge ile gorunmeli; blocked gate aciklamasi ve remediation linki okunmali; override aksiyonunda confirmation ve audit kaydi beklenmeli; refresh sonrasi gate state kalici olmali.

### 28. `/governance/proposals`

**Ne ise yarar:** Governance policy veya sistem degisikligi proposal'larini listeler ve karar surecine acar.

**Nereleri tetikler:** Proposal list API'si, proposal detail/decision aksiyonlari, retry veya sync fonksiyonlari.

**Ornek testler:** Proposal status filtreleri calismali; yeni proposal veya retry aksiyonu varsa validation test edilmeli; detail linkleri dogru id tasimali; rejected proposal icin gerekce alaninin render edildigini dogrula.

### 29. `/governance/safety`

**Ne ise yarar:** Governance safety kontrollerini, policy guard sonuclarini ve risk durumunu gosterir.

**Nereleri tetikler:** Safety summary endpoint'leri, policy violation listeleri, escalation/proof linkleri.

**Ornek testler:** Safety skor kartlari ve violation listesi dogru gorunmeli; critical violation varsa alert banner beklenmeli; ilgili proof veya escalation linkleri calismali; API hata aldiginda sayfa fail-closed mesaj vermeli.

### 30. `/governor`

**Ne ise yarar:** Governor karar, durum, case ve kontrol merkezidir.

**Nereleri tetikler:** Governor case/status API'leri, override/restore/execute aksiyonlari, alt route navigation ve audit/proof baglantilari.

**Ornek testler:** Governor summary ve aktif case listesi gorunmeli; override/restore gibi riskli aksiyonlarda confirmation zorunlu olmali; action sonucunda status, toast ve audit kaydi kontrol edilmeli; read-only rolde aksiyonlar disabled kalmali.

### 31. `/governor/alerts`

**Ne ise yarar:** Governor alert kayitlarini ve operator tarafindan ele alinmasi gereken uyarilari listeler.

**Nereleri tetikler:** Alert list API'si, ack/resolve/suppress aksiyonlari, `/governor/alerts/[id]` detay route'u.

**Ornek testler:** Alert severity ve status filtreleri dogru calismali; ack/resolve aksiyonlari listede status degistirmeli; detail link sample alert ile acilmali; bos alert listesinde sistem saglikli mesaji gorunmeli.

### 32. `/governor/drifts`

**Ne ise yarar:** Model, policy veya runtime drift sinyallerini listeler.

**Nereleri tetikler:** Drift event list API'si, severity filtreleri, `/governor/drifts/[id]` detay route'u ve remediation linkleri.

**Ornek testler:** Drift satirlarinda kaynak, confidence ve detected_at alanlari dogrulanmali; severity filtresi dogru sonuc vermeli; detail link gecerli id ile acilmali; yeni veri yoksa empty state sayfa yuksekligini bozmayacak sekilde gorunmeli.

### 33. `/governor/drifts/[id]`

**Ne ise yarar:** Tek drift olayinin kanitlarini, etkisini ve onerilen aksiyonlarini gosterir.

**Nereleri tetikler:** Drift detail fetch, remediation/proof linkleri, acknowledge veya escalation aksiyonlari.

**Ornek testler:** Gecerli id ile metrik, confidence ve evidence alanlari render edilmeli; acknowledge/escalate aksiyonunda payload ve sonuc kontrol edilmeli; gecersiz id not-found state vermeli; uzun evidence JSON'lari okunabilir ve scroll edilebilir kalmali.

### 34. `/governor/drills`

**Ne ise yarar:** Governor resilience drill senaryolarini baslatma ve sonuc izleme sayfasidir.

**Nereleri tetikler:** Drill list API'si, create/run aksiyonlari, sonuc timeline'i ve proof linkleri.

**Ornek testler:** Drill kartlari scenario, status ve last_run bilgisiyle gorunmeli; run aksiyonu loading state ve disabled tekrar tiklama korumasi kullanmali; basarili run sonrasi status yenilenmeli; failed drill icin log/detail linki calismali.

### 35. `/governor/escalations`

**Ne ise yarar:** Governor tarafindan uretilen escalation kayitlarini izler ve operator kararlarini toplar.

**Nereleri tetikler:** Escalation list/detail API'leri, assign/resolve/escalate aksiyonlari, governance audit kayitlari.

**Ornek testler:** Escalation satirlarinda owner, severity ve SLA bilgisi gorunmeli; resolve formunda aciklama validasyonu calismali; action sonrasi liste ve badge guncellenmeli; forbidden kullanicida endpoint'e request gitmedigi dogrulanmali.

### 36. `/governor/federated`

**Ne ise yarar:** Federated governor kaynaklarini ve cross-node karar uyumunu gosterir.

**Nereleri tetikler:** Federated governor status API'leri, node sync kartlari, conflict/proof linkleri.

**Ornek testler:** Node bazli status kartlari render edilmeli; sync lag uyarilari dogru gorunmeli; conflict linkleri ilgili route'a gitmeli; API partial failure durumunda saglam node'lar gorunmeye devam etmeli.

### 37. `/governor/[id]`

**Ne ise yarar:** Tek governor case veya karar kaydinin detay ekranidir.

**Nereleri tetikler:** Governor case detail fetch, case aksiyonlari, proof/event linkleri ve status refresh.

**Ornek testler:** Gecerli id ile case basligi, durum, owner ve evidence render edilmeli; case action butonlari dogru endpoint'i tetiklemeli; gecersiz id icin not-found state beklenmeli; detailden geri donus `/governor` sayfasina calismali.

### 38. `/governor/observability`

**Ne ise yarar:** Governor runtime gozlemlenebilirlik metriklerini, log ozetlerini ve saglik sinyallerini gosterir.

**Nereleri tetikler:** Observability metrics API'leri, timeline/log listeleri, filtre ve refresh kontrolleri.

**Ornek testler:** Metrik kartlari sayisal formatla gorunmeli; refresh butonu yeni network istegi atmali; log filtresi uygulandiginda liste guncellenmeli; chart veya timeline bos veride kirilmamali.

### 39. `/governor/outcomes`

**Ne ise yarar:** Governor kararlarinin sonuc ve etki metriklerini takip eder.

**Nereleri tetikler:** Outcome list/score API'leri, trend grafiklerini, scorecard/proof linklerini.

**Ornek testler:** Outcome kartlarinda success/failure oranlari dogru gorunmeli; zaman araligi filtresi varsa API query degismeli; detail/proof linkleri calismali; negatif veya eksik metriklerde UI formatlama hatasi vermemeli.

### 40. `/governor/proof`

**Ne ise yarar:** Governor proof event ve snapshot kaynaklarina genel giris saglar.

**Nereleri tetikler:** Proof summary API'leri, `/governor/proof/events`, `/governor/proof/snapshots` linkleri ve kanit kartlari.

**Ornek testler:** Event ve snapshot ozet sayilari dogru gorunmeli; her karttan ilgili alt route'a gidilmeli; proof API hata alirsa sayfa fail-safe mesaj vermeli; refresh sonrasi son kanit tarihi guncellenmeli.

### 41. `/governor/proof/events`

**Ne ise yarar:** Governor proof event kayitlarini listeler.

**Nereleri tetikler:** Proof events list API'si, event filtreleri, event detail expand ve snapshot linkleri.

**Ornek testler:** Event listesinde type, actor, timestamp ve hash alanlari gorunmeli; filtreler dogru sonuc vermeli; event expand metadata'yi okunabilir gostermeli; bozuk event payload'i UI'yi dusurmemeli.

### 42. `/governor/proof/snapshots`

**Ne ise yarar:** Governor proof snapshot kayitlarini listeler.

**Nereleri tetikler:** Snapshot list API'si, `/governor/proof/snapshots/[id]` detay linkleri, export/download aksiyonlari.

**Ornek testler:** Snapshot satirlarinda id, created_at, status ve hash gorunmeli; detail link gecerli id ile acilmali; export aksiyonu dogru dosya veya response status'u vermeli; bos listede empty state gorunmeli.

### 43. `/governor/proof/snapshots/[id]`

**Ne ise yarar:** Tek governor proof snapshot'in detay ve export yuzeyidir.

**Nereleri tetikler:** Snapshot detail fetch, export/download endpoint'i, proof event referanslari.

**Ornek testler:** Gecerli id ile snapshot metadata ve hash render edilmeli; export butonu network response'unu basariyla tamamlamali; gecersiz id not-found state vermeli; buyuk snapshot JSON'u scroll alaninda okunabilir kalmali.

### 44. `/governor/resilience`

**Ne ise yarar:** Governor resilience durumunu, dayanıklılık senaryolarini ve riskleri gosterir.

**Nereleri tetikler:** Resilience status API'si, drill/proof linkleri, remediation veya acknowledge aksiyonlari.

**Ornek testler:** Resilience skor ve risk kartlari dogru gorunmeli; drill linkleri `/governor/drills` route'una gitmeli; risk acknowledge aksiyonu status degistirmeli; service partial failure durumunda sayfa okunabilir kalmali.

### 45. `/governor/scorecard`

**Ne ise yarar:** Governor performans ve karar kalitesi skorlarini operatora ozetler.

**Nereleri tetikler:** Scorecard metrics API'leri, outcome/proof linkleri, grafik ve tablo render katmani.

**Ornek testler:** Scorecard metrikleri dogru formatla gorunmeli; trend grafikleri bos veride kirilmamali; outcome linkleri ilgili sayfaya gitmeli; filtre degisiminde network query ve render sonucu dogrulanmali.

### 46. `/identity`

**Ne ise yarar:** Kimlik, servis hesabi, key uretimi, quarantine ve recovery islemlerini yonetir.

**Nereleri tetikler:** `/api/v1/auth/identities`, `POST /api/v1/auth/identity/keys/generate?target_id=...`, `POST /api/v1/auth/identity/{id}/recover`, `POST /api/v1/auth/identity/{id}/quarantine`, role gate ve read-only guard.

**Ornek testler:** Read-only rolde sayfa console hatasi vermeden kisitli state gostermeli; admin rolde identity listesi ve aksiyon butonlari gorunmeli; key generate/quarantine/recover aksiyonlarinda confirmation, payload ve toast dogrulanmali; API 403 veya 500 durumunda aksiyon butonu kilitli kalmamali ve hata mesajı gorunmeli.

### 47. `/improvements`

**Ne ise yarar:** Sistem iyilestirme onerilerini, durumlarini ve operator kararlarini listeler.

**Nereleri tetikler:** Improvement list API'si, approve/reject/update aksiyonlari, repair-lab veya governance linkleri.

**Ornek testler:** Improvement satirlarinda priority, source ve status alanlari gorunmeli; approve/reject aksiyonlari status ve audit kaydi uretmeli; filtre/search varsa dogru calismali; bos liste durumunda uygun empty state beklenmeli.

### 48. `/incidents`

**Ne ise yarar:** Genel incident operasyon listesidir; olay takibi, filtreleme ve cozum akislarini baslatir.

**Nereleri tetikler:** Incident list API'si, create/resolve/reassign aksiyonlari, `/incidents/[id]` detay route'u.

**Ornek testler:** Open/high severity filtreleri dogru sonuc vermeli; incident row click detay sayfasina gitmeli; resolve/reassign aksiyonlarinda validation ve toast test edilmeli; invalid API response tabloyu dusurmemeli.

### 49. `/incidents/[id]`

**Ne ise yarar:** Tek incident icin detay, timeline, sorumlu ve cozum aksiyonlarini gosterir.

**Nereleri tetikler:** Incident detail fetch, comment/resolve/reopen endpoint'leri, timeline ve proof/governance linkleri.

**Ornek testler:** Gecerli id ile baslik, severity, owner ve timeline gorunmeli; resolve formu zorunlu aciklama istemeli; gecersiz id not-found state vermeli; cozum sonrasi status badge ve listeye donus state'i dogrulanmali.

### 50. `/learning/adaptation-candidates`

**Ne ise yarar:** Sistem tarafindan onerilen adaptation candidate kayitlarini inceler.

**Nereleri tetikler:** Adaptation candidate list API'si, approve/reject/promote aksiyonlari, learning evidence linkleri.

**Ornek testler:** Candidate kartlarinda confidence, source ve expected impact gorunmeli; approve/reject aksiyonu dogru payload ile gitmeli; confidence filtresi varsa sonuc dogrulanmali; dusuk confidence item'larinda warning state beklenmeli.

### 51. `/learning/fingerprints`

**Ne ise yarar:** Ogrenme ve davranis fingerprint kayitlarini listeler.

**Nereleri tetikler:** Fingerprint list API'si, `/learning/fingerprints/[id]` detay route'u, filtre/search ve metadata render.

**Ornek testler:** Fingerprint listesinde id, type, version ve last_seen alanlari gorunmeli; detail link gecerli id ile acilmali; search filtre sonucu dogru olmali; bos veri ve API hata state'leri test edilmeli.

### 52. `/learning/fingerprints/[id]`

**Ne ise yarar:** Tek fingerprint kaydinin detay, metrik ve baglam bilgisini gosterir.

**Nereleri tetikler:** Fingerprint detail fetch, related patterns/adaptation linkleri, metadata JSON render.

**Ornek testler:** Gecerli id ile fingerprint metadata ve metrikler gorunmeli; buyuk JSON alanlari tasma yapmamali; gecersiz id not-found state vermeli; related linkler dogru learning route'larina gitmeli.

### 53. `/learning/negative-patterns`

**Ne ise yarar:** Basarisiz veya riskli davranis pattern'lerini izler.

**Nereleri tetikler:** Negative pattern list API'si, suppression/remediation aksiyonlari, strategy memory linkleri.

**Ornek testler:** Pattern kartlari severity, frequency ve source ile gorunmeli; remediation linki ilgili sayfaya gitmeli; suppress aksiyonu confirmation ve audit gerektirmeli; bos veri state'i olumlu sistem mesajiyla gorunmeli.

### 54. `/learning/strategy-memory`

**Ne ise yarar:** Sistem strateji hafizasini, ogrenilmis karar kaliplarini ve gecmis sonuclari gosterir.

**Nereleri tetikler:** Strategy memory list/detail API'leri, search/filter, adaptation/fingerprint linkleri.

**Ornek testler:** Memory kayitlari title, scope ve updated_at ile render edilmeli; search query listeyi dogru daraltmali; detail expand uzun metinlerde okunabilir olmali; API hata durumunda retry davranisi test edilmeli.

### 55. `/login`

**Ne ise yarar:** Operator kimlik dogrulama ve gerekirse register/login akisinin giris sayfasidir.

**Nereleri tetikler:** Auth form state'i, login/register endpoint'leri, session cookie/token yazimi ve authenticated redirect.

**Ornek testler:** Gecerli credential ile login olup hedef sayfaya redirect bekle; hatali credential ile form seviyesinde hata gor; zorunlu alan ve email format validasyonlarini test et; login sonrasi protected route refresh edildiginde session'in korundugunu dogrula.

### 56. `/mcp-hub`

**Ne ise yarar:** MCP baglantilarini, tool durumlarini ve hub konfigurasyonunu gosterir.

**Nereleri tetikler:** MCP status/config API'leri, tool list render, enable/refresh aksiyonlari.

**Ornek testler:** Tool listesinde ad, durum ve son kontrol bilgisi gorunmeli; refresh aksiyonu yeni status fetch etmeli; down MCP icin alert ve retry gorunmeli; config veya enable aksiyonlarinda yetki kontrolu dogrulanmali.

### 57. `/meeting-room`

**Ne ise yarar:** Debate veya meeting room katilimcilarini ve canli oturum etkilesimini yonetir.

**Nereleri tetikler:** `/api/v1/debate/participants`, websocket baglantisi, participant join/leave state'i ve message/event timeline.

**Ornek testler:** Participant listesi yuklenmeli; websocket baglantisi acilip event alindiginda timeline guncellenmeli; websocket kapanirsa reconnect veya error state gorunmeli; katilimci yokken empty state layout'u bozmamali.

### 58. `/mesh`

**Ne ise yarar:** Mesh servis durumunu, node sagligini ve son mesh event'lerini gosterir.

**Nereleri tetikler:** `/api/v1/mesh/status`, `/api/v1/mesh/timeline?limit=15`, timeline render ve refresh kontrolleri.

**Ornek testler:** Mesh status kartlari node ve health bilgisiyle gorunmeli; timeline limit 15'i asmamali; refresh sonrasi son event tarihi guncellenmeli; status endpoint hata alirsa timeline yine kontrollu gorunmeli.

### 59. `/ops/handover-status`

**Ne ise yarar:** Operasyon handover hazirlik durumunu, eksikleri ve devralma sinyallerini gosterir.

**Nereleri tetikler:** Handover status API'si, checklist kartlari, launch gate veya incident linkleri.

**Ornek testler:** Checklist item'lari pass/fail durumuyla gorunmeli; blocked item linkleri ilgili detay sayfasina gitmeli; refresh butonu state'i yenilemeli; eksik veri durumunda fail-safe mesaj beklenmeli.

### 60. `/ops/launch-gates`

**Ne ise yarar:** Operasyon launch gate sonuc ve bloklayici kontrollerini izler.

**Nereleri tetikler:** Launch gate API'si, gate retry/ack aksiyonlari, compliance ve system-health linkleri.

**Ornek testler:** Gate status badge'leri dogru renk ve metinle render edilmeli; retry/ack aksiyonu network sonucuna gore toast vermeli; blocked gate aciklamasi gorunmeli; refresh sonrasi state tutarli kalmali.

### 61. `/policy-proposals`

**Ne ise yarar:** Policy proposal kayitlarini ve sync/retry durumlarini yonetir.

**Nereleri tetikler:** Policy proposal list API'si, retry sync aksiyonlari, governance proposal linkleri.

**Ornek testler:** Proposal listesinde status, owner ve updated_at gorunmeli; retry sync aksiyonu dogru endpoint'i tetiklemeli; failed proposal'da hata gerekcesi okunmali; filtre ve detail linkleri calismali.

### 62. `/project-factory`

**Ne ise yarar:** Project Factory portfolyo, proje uretimi, gate ve teslimat akisini yonetir.

**Nereleri tetikler:** `/api/v1/project-factory/...` portfolyo, catalog, project create/update, gate, cost ve artifact endpoint'leri; `/project-factory/[project_id]` detay route'u.

**Ornek testler:** Portfolio kartlari proje durumu ve gate bilgisiyle render edilmeli; yeni proje formunda required alan validasyonlari calismali; project detail linki gecerli id ile acilmali; create/update aksiyonlarinda optimistic UI, toast, list refresh ve API payload dogrulanmali.

### 63. `/prompt-studio`

**Ne ise yarar:** Harness agent prompt, policy ve agent config alanlarini inceleme/duzenleme yuzeyidir.

**Nereleri tetikler:** Harness agent list/detail API'leri, update formu, validation ve prompt preview/render katmani.

**Ornek testler:** Agent listesi role ve status bilgisiyle gorunmeli; agent secildiginde detail panel dolmali; prompt/config update validasyonlari ve save sonucunu test et; buyuk prompt metninde editor veya textarea tasma yapmamali.

### 64. `/proof/events`

**Ne ise yarar:** Genel proof event kayitlarini listeler.

**Nereleri tetikler:** Proof events API'si, event filtreleri, snapshot ve governance linkleri.

**Ornek testler:** Event satirlarinda type, timestamp, hash ve actor gorunmeli; filtreler ve pagination varsa dogru calismali; event detail expand metadata'yi okunabilir gostermeli; API hata durumunda retry test edilmeli.

### 65. `/proof/snapshots`

**Ne ise yarar:** Genel proof snapshot kayitlarini listeler.

**Nereleri tetikler:** Snapshot list API'si, `/proof/snapshots/[id]` detay route'u, export/download aksiyonlari.

**Ornek testler:** Snapshot listesi status ve hash ile render edilmeli; detail link gecerli id ile acilmali; export aksiyonu basarili response vermeli; bos liste ve hata state'leri ayri test edilmeli.

### 66. `/proof/snapshots/[id]`

**Ne ise yarar:** Tek proof snapshot'in detay, metadata ve export ekranidir.

**Nereleri tetikler:** Snapshot detail fetch, export endpoint'i, related event/proof linkleri.

**Ornek testler:** Gecerli id ile snapshot metadata gorunmeli; hash veya integrity bilgisi dogrulanmali; export butonu dosya/response uretmeli; gecersiz id not-found state vermeli.

### 67. `/repair-lab`

**Ne ise yarar:** Repair case, benchmark, PR agent, autonomous repair ve apply aksiyonlarinin ana laboratuvaridir.

**Nereleri tetikler:** `/api/v1/repair-lab/...` case, benchmark, apply, PR-agent, trigger-autonomous-repair, verifier ve evolution endpoint'leri.

**Ornek testler:** Repair case listesi status ve severity ile gorunmeli; trigger/apply gibi state degistiren aksiyonlar confirmation ve yetki kontrolu istemeli; benchmark sonuc kartlari dogru render edilmeli; failed repair durumunda log/detail linki ve retry state test edilmeli.

### 68. `/repair-lab/improvements`

**Ne ise yarar:** Repair Lab kapsamindaki improvement onerilerini ve uygulama durumlarini izler.

**Nereleri tetikler:** Improvement repair API'leri, apply/approve/reject aksiyonlari, repair case ve self-tuning linkleri.

**Ornek testler:** Improvement kartlari source, impact ve status ile gorunmeli; apply aksiyonunda payload ve sonuc dogrulanmali; rejected item'larda gerekce gorunmeli; liste bosken operatora uygun empty state verilmeli.

### 69. `/repair-memory`

**Ne ise yarar:** Repair gecmisi, heatmap, tekrar eden hata kaliplari ve ogrenme sinyallerini gosterir.

**Nereleri tetikler:** Repair memory/heatmap API'leri, pattern detail linkleri, filtre ve grafik render katmani.

**Ornek testler:** Heatmap veya pattern listesi dogru renk ve degerlerle render edilmeli; filtre degisimi grafik/list sonucunu guncellemeli; bos veri grafik alanini bozmamali; related repair case linkleri calismali.

### 70. `/safety`

**Ne ise yarar:** Sistem safety durumunu, policy guard sinyallerini ve risk uyarilarini ozetler.

**Nereleri tetikler:** Safety summary API'si, violation listeleri, governance/safety linkleri ve escalation aksiyonlari.

**Ornek testler:** Safety skor ve violation kartlari dogru render edilmeli; critical risk varsa banner gorunmeli; ilgili governance linkleri calismali; safety API hata alirsa fail-closed mesaj ve retry state test edilmeli.

### 71. `/self-tuning`

**Ne ise yarar:** Self-tuning onerileri, evolution feed ve tuning aksiyonlarini yonetir.

**Nereleri tetikler:** `/api/v1/repair-lab/tuning/suggestions`, `/api/v1/repair-lab/evolution/feed`, `/api/v1/repair-lab/evolution/status`, apply suggestion endpoint'i.

**Ornek testler:** Suggestion listesinde confidence, scope ve status gorunmeli; apply aksiyonunda confirmation, API payload ve toast dogrulanmali; evolution feed bos veya hata durumunda UI stabil kalmali; role gate read-only kullanicida apply butonunu devre disi birakmali.

### 72. `/self-tuning/scoped`

**Ne ise yarar:** Belirli scope icin self-tuning onerilerini ve sinirli uygulama akislarini gosterir.

**Nereleri tetikler:** Scoped tuning API'leri, scope selector, apply/preview aksiyonlari ve self-tuning status endpoint'leri.

**Ornek testler:** Scope secimi liste ve onerileri guncellemeli; preview/apply aksiyonlari dogru scope ile gitmeli; scope bos veya gecersizse validation gorunmeli; basarili apply sonrasi status yenilenmeli.

### 73. `/system-health`

**Ne ise yarar:** Runtime health, queue diagnostics, servis sagligi ve self-repair aksiyonlarini izler.

**Nereleri tetikler:** `/health/dashboard`, `/health/runtime-diagnostics`, `/health/queue-detailed`, `POST /health/queue-scale`, runtime diagnostic repair endpoint'leri.

**Ornek testler:** Health kartlari servis bazli status gostermeli; queue scale formunda numeric validation calismali; diagnostic repair aksiyonunda confirmation ve sonuc toast'u beklenmeli; bir health endpoint'i hata alirken diger kartlarin render edilmeye devam ettigini dogrula.

### 74. `/training`

**Ne ise yarar:** Training/drill senaryolarini ve egitim akislarini listeler.

**Nereleri tetikler:** Training/drill list API'si, trigger/start aksiyonlari, sonuc ve progress state'leri.

**Ornek testler:** Training kartlari scenario, status ve last_run ile gorunmeli; start/trigger aksiyonunda loading ve duplicate-click korumasi calismali; tamamlanan training sonucu listede guncellenmeli; failed training detay linki calismali.

### 75. `/ui-repair`

**Ne ise yarar:** UI repair monitoring, route audit, case, smoke, repair ve apply aksiyonlarinin kontrol panelidir.

**Nereleri tetikler:** `/api/v1/ui-repair/...` monitoring, routes, cases, runtime guard, smoke, repair/apply endpoint'leri ve Playwright/repair kanit yuzeyleri.

**Ornek testler:** Route monitoring listesi status ve son audit bilgisiyle gorunmeli; smoke veya repair aksiyonu confirmation, loading ve sonuc state'i uretmeli; failed case detail/log linkleri calismali; apply aksiyonlarinda read-only/admin role gate, payload ve audit kaniti dogrulanmali.

### 76. `/verifiers`

**Ne ise yarar:** Verifier kayitlarini, repair-lab dogrulama durumlarini ve kalite kapilarini listeler.

**Nereleri tetikler:** Verifier list/status API'leri, run/refresh aksiyonlari, repair-lab ve proof linkleri.

**Ornek testler:** Verifier satirlarinda name, status, last_run ve coverage gorunmeli; run aksiyonu dogru endpoint'i tetiklemeli; failed verifier icin log/proof linki calismali; bos liste durumunda sistem mesajı gorunmeli.

### 77. `/workflows`

**Ne ise yarar:** Workflow listesini, istatistiklerini ve gorev operasyonlarini gosterir.

**Nereleri tetikler:** Workflow list/stats API'leri, `/workflows/[id]` detay route'u, create route linki ve approval/task aksiyonlari.

**Ornek testler:** Workflow tablosunda id, status, owner ve updated_at gorunmeli; filtre/search ve pagination dogru calismali; create butonu `/workflows/create` route'una gitmeli; row detail linki dogru workflow id ile acilmali.

### 78. `/workflows/[id]`

**Ne ise yarar:** Tek workflow icin detay, task, approval ve karar aksiyonlarini gosterir.

**Nereleri tetikler:** Workflow detail fetch, approve/reassign/pending approval decision endpoint'leri, task timeline ve audit linkleri.

**Ornek testler:** Gecerli id ile workflow basligi, status ve task listesi render edilmeli; approve/reassign aksiyonlarinda form validation, payload ve status refresh kontrol edilmeli; gecersiz id not-found state vermeli; pending approval alanlari governance approval linkleriyle tutarli olmali.

### 79. `/workflows/create`

**Ne ise yarar:** Yeni workflow veya task akisi olusturma formudur.

**Nereleri tetikler:** Workflow create endpoint'i, form validation, template/owner selector ve create sonrasi redirect veya toast.

**Ornek testler:** Zorunlu alanlar bosken submit engellenmeli; valid payload ile create istegi dogru body ile gitmeli; basarili create sonrasi yeni workflow detayina veya listeye redirect test edilmeli; backend validation hatalari alan bazli gorunmeli.

### 80. `/governor/alerts/[id]`

**Ne ise yarar:** Tek governor alert kaydinin detay, kanit ve cozum aksiyonlarini gosterir.

**Nereleri tetikler:** Alert detail fetch, ack/resolve/suppress endpoint'leri, related governor case/proof linkleri.

**Ornek testler:** Once test seed ile en az bir alert olustur ve `page_audit.py` sample discovery'nin id buldugunu dogrula; gecerli id ile severity, source ve evidence alanlari gorunmeli; ack/resolve aksiyonlarinda status refresh ve audit kaydi beklenmeli; gecersiz id not-found state vermeli. Son baseline'da bu route `skipped_no_sample` oldugu icin seed olmadan pass/fail karari verilmemeli.

### 81. `/project-factory/[project_id]`

**Ne ise yarar:** Tek Project Factory projesinin detay, gate, maliyet, artifact ve operasyon aksiyonlarini gosterir.

**Nereleri tetikler:** `/api/v1/project-factory/...` project detail, gate update, artifact, cost, status transition ve portfolio refresh endpoint'leri.

**Ornek testler:** Once test seed ile portfolio icinde gecerli bir `project_id` olustur ve route sample discovery'nin bunu buldugunu dogrula; detay sayfasinda proje metadata, gate ve artifact listesi gorunmeli; status/gate aksiyonlarinda validation, payload, toast ve audit sonucu test edilmeli; gecersiz `project_id` not-found state vermeli. Son baseline'da bu route `skipped_no_sample` oldugu icin seed zorunludur.

## Otomasyon Onceligi

1. `page_audit.py` icin route discovery + console/page error regresyon testi korunmali.
2. Dinamik route seed eksikleri once `/governor/alerts/[id]` ve `/project-factory/[project_id]` icin kapatilmali.
3. State degistiren sayfalar icin Playwright network intercept ile method, URL, payload ve toast sonucu dogrulanmali.
4. Role-gated yuzeyler icin en az iki persona calistirilmali: read-only observer ve admin/operator.
5. Telegram onay akisina baglanan approval/workflow testleri icin callback payload parse ve fake callback smoke ayrica kosulmali.
