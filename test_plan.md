# 🧪 Sovereign AGI Control Plane — Sayfa Bazlı Test Planları

> **Proje:** Sovereign AGI Control Plane (Refine + Next.js)  
> **Tarih:** 2026-07-02  
> **Versiyon:** v12.1  
> **Test Ortamı:** `http://localhost:3100`  
> **Kaynak Dizin:** `apps/refine_control_plane/src/app/`

> [!IMPORTANT]
> Bu test planları, kaynak kod analizi sonucu gerçek UI elementleri, API endpoint'leri ve etkileşim noktalarına dayanarak oluşturulmuştur. Her sayfa için sayfanın amacı, tıklanabilir/etkileşimli elementler ve adım adım örnek test senaryoları bulunmaktadır.

---



## 📑 İçindekiler

### Ana Sayfalar & Kök Dizinler (1 - 33)
| # | Sayfa | Route | Durum |
|---|-------|-------|-------|
| 1 | [Dashboard (Ana Sayfa)](#1-dashboard-ana-sayfa) | `/` | ✅ Var |
| 2 | [Login](#2-login) | `/login` | ✅ Var |
| 3 | [Approvals](#3-approvals) | `/approvals` | ✅ Var |
| 4 | [Audit](#4-audit) | `/audit` | ✅ Var |
| 5 | [Axiology](#5-axiology) | `/axiology` | ✅ Var |
| 6 | [BilgeAPI Ops](#6-bilgeapi-ops) | `/bilgeapi-ops` | ✅ Var (1930 satır!) |
| 7 | [Calibrations](#7-calibrations) | `/calibrations` | ✅ Var |
| 8 | [Compliance](#8-compliance) | `/compliance` | ✅ Var |
| 9 | [Costs](#9-costs) | `/costs` | ✅ Var |
| 10 | [Evolution](#10-evolution) | `/evolution` | ✅ Var |
| 11 | [Federation](#11-federation) | `/federation` | ✅ Var (Hardcoded data) |
| 12 | [Fleet](#12-fleet) | `/fleet` | ✅ Var |
| 13 | [Governor](#13-governor) | `/governor` | ✅ Var |
| 14 | [Identity](#14-identity) | `/identity` | ✅ Var |
| 15 | [Improvements](#15-improvements) | `/improvements` | ✅ Var |
| 16 | [Incidents](#16-incidents) | `/incidents` | ✅ Var |
| 17 | [MCP Hub](#17-mcp-hub) | `/mcp-hub` | ✅ Var |
| 18 | [Meeting Room](#18-meeting-room) | `/meeting-room` | ✅ Var (WebSocket) |
| 19 | [Mesh](#19-mesh) | `/mesh` | ✅ Var (5sn polling) |
| 20 | [Policy Proposals](#20-policy-proposals) | `/policy-proposals` | ✅ Var |
| 21 | [Project Factory](#21-project-factory) | `/project-factory` | ✅ Var (1274 satır client) |
| 22 | [Prompt Studio](#22-prompt-studio) | `/prompt-studio` | ✅ Var |
| 23 | [Proof Events](#23-proof-events) | `/proof/events` | ✅ Var |
| 24 | [Proof Snapshots](#24-proof-snapshots) | `/proof/snapshots` | ✅ Var |
| 25 | [Repair Lab](#25-repair-lab) | `/repair-lab` | ✅ Var |
| 26 | [Repair Memory](#26-repair-memory) | `/repair-memory` | ✅ Var |
| 27 | [Safety](#27-safety) | `/safety` | ✅ Var (Statik state) |
| 28 | [Self-Tuning](#28-self-tuning) | `/self-tuning` | ✅ Var |
| 29 | [System Health](#29-system-health) | `/system-health` | ✅ Var |
| 30 | [Training](#30-training) | `/training` | ✅ Var |
| 31 | [UI Repair](#31-ui-repair) | `/ui-repair` | ✅ Var (73KB, 20+ tab!) |
| 32 | [Verifiers](#32-verifiers) | `/verifiers` | ✅ Var |
| 33 | [Workflows](#33-workflows) | `/workflows` | ✅ Var |

### 📂 Operasyon & Yönetişim Alt Sayfaları (34 - 37)
| # | Sayfa | Route | Durum |
|---|-------|-------|-------|
| 34 | [Ops: Handover Status (Rollout Center)](#34-ops-handover-status-rollout-center) | `/ops/handover-status` | ✅ Var |
| 35 | [Ops: Launch Gates](#35-ops-launch-gates) | `/ops/launch-gates` | ✅ Var |
| 36 | [Compliance: Audit Bundles](#36-compliance-audit-bundles) | `/compliance/audit-bundles` | ✅ Var |
| 37 | [Governance: Lineage](#37-governance-lineage) | `/governance/lineage` | ✅ Var |

### 🛡️ Governor & Güvenlik Alt Sayfaları (38 - 47)
| # | Sayfa | Route | Durum |
|---|-------|-------|-------|
| 38 | [Governor: Observability Dashboard](#38-governor-observability-dashboard) | `/governor/observability` | ✅ Var |
| 39 | [Governor: Scorecard](#39-governor-scorecard) | `/governor/scorecard` | ✅ Var |
| 40 | [Governor: Proof Fabric](#40-governor-proof-fabric) | `/governor/proof` | ✅ Var |
| 41 | [Governor: Alerts Center](#41-governor-alerts-center) | `/governor/alerts` | ✅ Var |
| 42 | [Governor: Behavioral Drift Monitor](#42-governor-behavioral-drift-monitor) | `/governor/drifts` | ✅ Var |
| 43 | [Governor: Chaos Engineering Lab (Resilience Drills)](#43-governor-chaos-engineering-lab-resilience-drills) | `/governor/drills` | ✅ Var |
| 44 | [Governor: Aktif Eskalasyonlar](#44-governor-aktif-eskalasyonlar) | `/governor/escalations` | ✅ Var |
| 45 | [Governor: Federated Governance View](#45-governor-federated-governance-view) | `/governor/federated` | ✅ Var |
| 46 | [Governor: Outcomes](#46-governor-outcomes) | `/governor/outcomes` | ✅ Var |
| 47 | [Governor: Operational Resilience](#47-governor-operational-resilience) | `/governor/resilience` | ✅ Var |

### 🧠 Öğrenme & Filo Alt Sayfaları (48 - 54)
| # | Sayfa | Route | Durum |
|---|-------|-------|-------|
| 48 | [Learning: Adaptation Candidates](#48-learning-adaptation-candidates) | `/learning/adaptation-candidates` | ✅ Var |
| 49 | [Learning: Error Fingerprints Ledger](#49-learning-error-fingerprints-ledger) | `/learning/fingerprints` | ✅ Var |
| 50 | [Learning: Negative Patterns Blacklist](#50-learning-negative-patterns-blacklist) | `/learning/negative-patterns` | ✅ Var |
| 51 | [Learning: Strategy Memory](#51-learning-strategy-memory) | `/learning/strategy-memory` | ✅ Var |
| 52 | [Fleet: Agent Registry](#52-fleet-agent-registry) | `/fleet/agents` | ✅ Var |
| 53 | [Fleet: Operations Controls](#53-fleet-operations-controls) | `/fleet/operations` | ✅ Var |
| 54 | [Federation: Domain Conflict Management](#54-federation-domain-conflict-management) | `/federation/conflicts` | ✅ Var |

### 🔀 Dinamik Detay & Akış Sayfaları (55 - 66)
| # | Sayfa | Route | Durum |
|---|-------|-------|-------|
| 55 | [Approvals Detail Page](#55-approvals-detail-page) | `/approvals/[id]` | ✅ Var |
| 56 | [Axiology Detail Page](#56-axiology-detail-page) | `/axiology/[id]` | ✅ Var |
| 57 | [Governor Alerts Detail Page](#57-governor-alerts-detail-page) | `/governor/alerts/[id]` | ✅ Var |
| 58 | [Governor Drifts Detail Page](#58-governor-drifts-detail-page) | `/governor/drifts/[id]` | ✅ Var |
| 59 | [Governor Proof Snapshot Detail Page](#59-governor-proof-snapshot-detail-page) | `/governor/proof/snapshots/[id]` | ✅ Var |
| 60 | [Governor Case Override & Escalation Detail](#60-governor-case-override-escalation-detail) | `/governor/[id]` | ✅ Var |
| 61 | [Incident Detail & Mitigation Client](#61-incident-detail-mitigation-client) | `/incidents/[id]` | ✅ Var |
| 62 | [Learning Fingerprint Recurrence Detail](#62-learning-fingerprint-recurrence-detail) | `/learning/fingerprints/[id]` | ✅ Var |
| 63 | [Project Factory Client Rollout Board](#63-project-factory-client-rollout-board) | `/project-factory/[project_id]` | ✅ Var |
| 64 | [Workflow Detail Progress Trace](#64-workflow-detail-progress-trace) | `/workflows/[id]` | ✅ Var |
| 65 | [Workflow Create Form](#65-workflow-create-form) | `/workflows/create` | ✅ Var |
| 66 | [Self-Tuning Scoped Calibration Table](#66-self-tuning-scoped-calibration-table) | `/self-tuning/scoped` | ✅ Var |

### Sistem Genelindeki Testler (67)
| # | Sayfa | Route | Durum |
|---|-------|-------|-------|
| 67 | [Cross-Page Testleri](#67-cross-page-testleri) | — | — |

> [!NOTE]
> **Var olmayan root page'ler:** `governance/page.tsx` (sadece alt dizinler), `learning/page.tsx` (4 alt sayfa var: adaptation-candidates, fingerprints, negative-patterns, strategy-memory), `ops/page.tsx` (2 alt sayfa var: handover-status, launch-gates). Bu sayfalar ayrı test planı gerektirir.

---


## 1. Dashboard (Ana Sayfa)

### 📌 Sayfanın Amacı
Sovereign AGI platformunun merkezi kontrol paneli. Sistem sağlığı, iş akışları, maliyetler, yönetişim durumu ve otonom onarım verilerini 5 sekmeli bir yapıda gösterir. CEO önerileri, runtime diagnostikleri ve self-repair çalışma durumlarını içerir. **Her 5 saniyede otomatik yenilenir.**

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | 5 Ana Sekme | Tab Bar | Overview, Workflows, Events, Health, Economy |
| 2 | MetricCards | Kart | Health score, active agents, API latency, DB status, workflows, cost/budget, canary success, governance |
| 3 | LiveEventStream | Bileşen | Canlı olay akışı |
| 4 | ApiHub | Bileşen | API hub paneli |
| 5 | DashboardCommandPanel | Bileşen | Komut paneli |
| 6 | LaunchEvidencePanel | Bileşen | Lansman kanıt paneli |
| 7 | EvolutionTimeline | Bileşen | Evrim zaman çizelgesi |
| 8 | CEO Suggestions paneli | Panel + Modal | Approve/Reject/Defer/War Room/Request Evidence aksiyonları — modal ile onay |
| 9 | Runtime Diagnostics kartları | Kart | Severity göstergeleri + Repair butonları |
| 10 | Self-Repair Runs paneli | Panel | Oto-onarım çalışma durumları |
| 11 | TaskFlow Runs paneli | Panel | İş akışı çalışma durumları |
| 12 | "Trigger Audit" butonu | Buton | Tam denetim çalıştırır |

### ✅ Test Senaryoları

#### TC-DASH-001: Sayfa Yüklenme ve Sekmeler
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `http://localhost:3100` adresini aç | Dashboard yüklenir, "Overview" sekmesi aktif |
| 2 | MetricCards'ları kontrol et | Health score, active agents, API latency, DB status kartları sayısal değerlerle dolu |
| 3 | "Workflows" sekmesine tıkla | İş akışı verileri gösterilir |
| 4 | "Events" sekmesine tıkla | LiveEventStream canlı olay akışını gösterir |
| 5 | "Health" sekmesine tıkla | Sağlık verileri gösterilir |
| 6 | "Economy" sekmesine tıkla | Maliyet/bütçe verileri gösterilir |

#### TC-DASH-002: CEO Suggestions — Approve Akışı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | CEO Suggestions panelini bul | En az 1 öneri kartı görünür |
| 2 | Bir önerinin "Approve" butonuna tıkla | Modal açılır: operator ID, gerekçe (rationale), risk onayı (acknowledgement) formu |
| 3 | Operator ID: "admin" gir | Alan dolar |
| 4 | Rationale: "Performans kazancı yeterli, risk düşük" gir | Alan dolar |
| 5 | Risk onay checkbox'ını işaretle | Checkbox işaretlenir |
| 6 | "Onayla" butonuna tıkla | `POST /api/v1/ceo/suggestions/{id}/approve` çağrılır, modal kapanır, öneri güncellenir |

#### TC-DASH-003: CEO Suggestions — Reject Akışı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir önerinin "Reject" butonuna tıkla | Modal açılır |
| 2 | Gerekçe: "Güvenlik riski çok yüksek, alternatif araştırılmalı" gir | Alan dolar |
| 3 | "Reddet" tıkla | `POST /api/v1/ceo/suggestions/{id}/reject` çağrılır |

#### TC-DASH-004: CEO Suggestions — War Room ve Defer
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "War Room" butonuna tıkla | Savaş odası akışı tetiklenir, modal açılır |
| 2 | "Defer" butonuna tıkla | Erteleme işlemi gerçekleşir |
| 3 | "Request Evidence" butonuna tıkla | Ek kanıt talebi gönderilir |

#### TC-DASH-005: Runtime Diagnostics Repair
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Runtime Diagnostics kartlarını kontrol et | Severity (error/warning/info) göstergeleri mevcut |
| 2 | "Repairable" etiketli bir kartın "Repair" butonuna tıkla | Onarım işlemi başlar, loading gösterilir |
| 3 | İşlem tamamlanır | Kart güncellenir, sorun "Fixed" olarak işaretlenir |

#### TC-DASH-006: Trigger Audit
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Trigger Audit" butonuna tıkla | `POST /api/v1/ceo/trigger-audit` çağrılır |
| 2 | Denetim başlar | Loading gösterilir, sonuç döndüğünde bilgi güncellenir |

#### TC-DASH-007: Otomatik Yenileme (5 saniye)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Dashboard'ı aç ve 15 saniye bekle | En az 2 kez otomatik API çağrısı yapılmalı (`/health/dashboard` her 5sn) |
| 2 | Network sekmesini kontrol et | Periyodik fetch istekleri görünür |

---

## 2. Login

### 📌 Sayfanın Amacı
Kontrol paneline giriş/kayıt sayfası. Ant Design bileşenleri ile çift modlu form (Login / Register). Refine auth provider ile JWT token alır. `?expired=true` URL parametresi ile oturum süresi dolmuş uyarısı gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | E-posta input | Input | E-posta girişi (email validasyonu) |
| 2 | Şifre input | Password Input | Maskeli şifre (register'da min 6 karakter) |
| 3 | Kullanıcı adı input | Input | Sadece register modunda görünür |
| 4 | "Beni hatırla" checkbox | Checkbox | Login modunda |
| 5 | "Şifremi unuttum" linki | Link | Stub (işlevsel değil) |
| 6 | "OTURUM AÇ" butonu | Submit Buton | Login formu gönderir |
| 7 | "KAYIT OL" butonu | Submit Buton | Register formu gönderir |
| 8 | Login/Register toggle linkleri | Link | Modlar arası geçiş |
| 9 | Hata/Başarı Alert banner | Alert | İşlem sonucu mesajları |
| 10 | Logo + "SOVEREIGN AGI" branding | Header | RocketOutlined ikonu |
| 11 | Footer güvenlik göstergeleri | Footer | SafetyOutlined + "SIF-01 IDENTITY PROTOCOL ACTIVE" |

### ✅ Test Senaryoları

#### TC-LOGIN-001: Başarılı Giriş
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/login` sayfasını aç | Ant Design Card ile login formu görünür, logo ve "SOVEREIGN AGI" başlığı mevcut |
| 2 | E-posta alanına `admin@sovereign.ai` yaz | Alan dolar |
| 3 | Şifre alanına `Bilgehan2024!` yaz | Alan maskeli şekilde dolar |
| 4 | "OTURUM AÇ" butonuna tıkla | Refine `useLogin()` tetiklenir, başarılıysa dashboard'a yönlendirilir |
| 5 | Footer'ı kontrol et | "SIF-01 IDENTITY PROTOCOL ACTIVE" yazısı ve güvenlik ikonları görünür |

#### TC-LOGIN-002: Hatalı Şifre ile Giriş
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | E-posta: `admin@sovereign.ai` gir | Alan dolar |
| 2 | Şifre: `yanlis_sifre_123` gir | Alan dolar |
| 3 | "OTURUM AÇ" tıkla | Hata Alert banner gösterilir: "Kullanıcı adı veya şifre hatalı" (kırmızı) |
| 4 | Form alanlarını kontrol et | E-posta korunmuş, şifre alanı görünür durumda |

#### TC-LOGIN-003: Boş Form Gönderimi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Hiçbir alan doldurmadan "OTURUM AÇ" tıkla | Ant Design form validasyonu tetiklenir: "Bu alan gerekli" mesajları |
| 2 | Sadece e-postayı doldur, şifreyi boş bırak | Şifre alanında validasyon hatası |
| 3 | Geçersiz e-posta formatı gir: "admin" | E-posta validasyon hatası |

#### TC-LOGIN-004: Register Moduna Geçiş
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Kayıt ol" toggle linkine tıkla | Form register moduna geçer, kullanıcı adı alanı eklenir |
| 2 | Kullanıcı adı: "testuser" gir | Alan dolar |
| 3 | E-posta: `test@sovereign.ai` gir | Alan dolar, email validasyonu geçerli |
| 4 | Şifre: `123` gir (5 karakter altı) | Min 6 karakter validasyon hatası gösterilir |
| 5 | Şifre: `Test123!` gir | Validasyon geçer |
| 6 | "KAYIT OL" tıkla | Refine `useRegister()` tetiklenir, başarılıysa success Alert gösterilir |

#### TC-LOGIN-005: Oturum Süresi Dolmuş Uyarı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/login?expired=true` adresini aç | "Oturumunuz sona erdi" uyarı mesajı gösterilir |
| 2 | Normal `/login` aç | Uyarı mesajı gösterilmez |

#### TC-LOGIN-006: Beni Hatırla
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Beni hatırla" checkbox'ını işaretle | Checkbox aktif |
| 2 | Başarılı giriş yap | Token kalıcı olarak saklanır |
| 3 | Tarayıcıyı kapat ve tekrar aç | Oturum aktif kalmalı |

---

## 3. Approvals

### 📌 Sayfanın Amacı
L3-L4 güvenlik kapısı onay/red geçidi. Quorum bazlı onay sistemi ile bekleyen yönetişim taleplerini onaylar veya reddeder. Acil direktif yayınlama özelliği ve Telegram bot entegrasyonu içerir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + "L3-L4 Gates" badge | Header | Karar bütünlüğü göstergesi (99.9% Verified) |
| 2 | "New Directive" butonu | Buton | Acil direktif modal açar |
| 3 | EliteApprovalCard kartları | Kart | Request type, reason, project, agent ID, timestamp, TX_ID hash |
| 4 | "Mobil Onay Destekli" badge | Badge | Her kartta |
| 5 | Approve / Reject butonları | Buton | Her onay kartında |
| 6 | Quorum State paneli (sağ bar) | Panel | Global konsensüs eşiği (4/5 sync) + ilerleme çubukları |
| 7 | Telegram Bot linki | Link | `https://t.me/SovereignAgiBot` |
| 8 | İstatistik paneli | Panel | Ort. karar süresi (12.4m), red oranı (2.1%), konsensüs drift |
| 9 | Emergency Directive modal | Modal | Scope selector + textarea + Broadcast/Abort |

### ✅ Test Senaryoları

#### TC-APPR-001: Bekleyen Onayları Görüntüleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/approvals` sayfasını aç | ResourceHeader "L3-L4 Gates" badge ile yüklenir |
| 2 | EliteApprovalCard kartlarını kontrol et | Her kartta: request type, reason, project scope, agent ID, timestamp, TX_ID hash bilgileri dolu |
| 3 | "Mobil Onay Destekli" badge'ini kontrol et | Her kartta mevcut |
| 4 | Karar bütünlüğü göstergesini kontrol et | "99.9% Verified" veya benzeri bir yüzde |

#### TC-APPR-002: Talep Onaylama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir onay kartının "Approve" butonuna tıkla | `PATCH /governance/approvals/{id}` çağrılır, `{status: "approved", comment: ...}` gönderilir |
| 2 | Kartın durumunu kontrol et | Kart "Approved" durumuna güncellenir veya listeden kaybolur |
| 3 | Quorum State panelini kontrol et | Konsensüs sayacı güncellenmeli |

#### TC-APPR-003: Talep Reddetme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir kartın "Reject" butonuna tıkla | `PATCH /governance/approvals/{id}` çağrılır, `{status: "rejected", comment: ...}` gönderilir |
| 2 | Red işlemi sonrası listeyi kontrol et | Kart güncellenir |

#### TC-APPR-004: Acil Direktif Yayınlama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "New Directive" butonuna tıkla | Emergency Directive modal açılır |
| 2 | Scope: "Fleet-Wide" seç | Radio buton seçilir |
| 3 | Executive order textarea'ya yaz: "Tüm ajanları güvenlik taramasından geçir — kritik açık tespit edildi" | Alan dolar |
| 4 | "Broadcast" butonuna tıkla | Direktif yayınlanır, modal kapanır |
| 5 | "Abort" butonuna tıkla (iptal test) | Modal kapanır, hiçbir işlem yapılmaz |

#### TC-APPR-005: Scope Seçimi — Local Node
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Modal'da Scope: "Local Node" seç | Radio buton değişir |
| 2 | Direktif yaz ve "Broadcast" tıkla | Sadece local node'a yayınlanır |

#### TC-APPR-006: Telegram Bot Linki
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sağ sidebar'daki Telegram Bot linkini kontrol et | `https://t.me/SovereignAgiBot` adresine yönlendiren link mevcut |
| 2 | Linke tıkla | Yeni sekmede Telegram bot sayfası açılır |

#### TC-APPR-007: İstatistik Paneli
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sağ sidebar'daki istatistik panelini kontrol et | Ort. karar süresi, red oranı, konsensüs drift değerleri görünür |
| 2 | Değerlerin mantıklılığını kontrol et | Karar süresi: pozitif sayı+dakika, red oranı: %0-100, drift: "Nominal" veya uyarı |

#### TC-APPR-008: Hata/Boş Durum
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | API hatası simüle et (backend kapalı) | Hata durumu gösterilir, "Consensus" retry butonu mevcut |
| 2 | "Consensus" retry butonuna tıkla | Veri yeniden çekilir |
| 3 | Hiç bekleyen onay yoksa | Boş durum mesajı gösterilir |

---

## 4. Audit

### 📌 Sayfanın Amacı
Değiştirilemez denetim izi / lineage görüntüleyicisi. Karar köken kayıtlarını (lineage records) ve kriptografik bütünlük anlık görüntülerini (proof snapshots) gösterir. "Institutional Grade" kalite damgası taşır.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + "Institutional Grade" badge | Header | Lineage durumu (SEALED & SYNCED / CHAIN ACTIVE) |
| 2 | "Export Proof" linki | Link | `/proof/snapshots` sayfasına yönlendirir |
| 3 | Live Verification Stream (sol sütun) | Timeline | Lineage kayıtları listesi |
| 4 | Lineage kayıt kartları | Kart | Timestamp, decision type badge, component, summary, integrity hash, confidence, outcome |
| 5 | Genişletilebilir detay | Accordion | Tam integrity hash + "Full Audit Trail" linki |
| 6 | Governance paneli (sağ bar) | Panel | Lineage kayıt sayısı, proof snapshot sayısı, son snapshot adı/durumu |
| 7 | Integrity Check paneli (sağ bar) | Panel | Son proof snapshot hash, event count, seal status |

### ✅ Test Senaryoları

#### TC-AUDIT-001: Lineage Kayıtlarını Görüntüleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/audit` sayfasını aç | ResourceHeader "Institutional Grade" badge ile yüklenir |
| 2 | Lineage state göstergesini kontrol et | "SEALED & SYNCED" veya "CHAIN ACTIVE" gösterilmeli |
| 3 | Live Verification Stream'deki kayıtları kontrol et | Her kayıtta timestamp, decision type badge, component adı mevcut |
| 4 | İlk kaydın summary kartını kontrol et | Rationale, integrity hash, confidence score, outcome bilgileri dolu |

#### TC-AUDIT-002: Kayıt Detayı Genişletme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir lineage kaydına tıkla | Kayıt seçili/genişletilmiş duruma geçer |
| 2 | Tam integrity hash'i kontrol et | Kriptografik hash formatında uzun bir string |
| 3 | "Full Audit Trail" linkini kontrol et | `/governor/proof` sayfasına yönlendiren link mevcut |

#### TC-AUDIT-003: Export Proof Butonu
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Export Proof" linkine tıkla | `/proof/snapshots` sayfasına yönlendirilir |

#### TC-AUDIT-004: Sağ Sidebar Panelleri
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Governance panelini kontrol et | Lineage records count, proof snapshots count, latest snapshot name, status bilgileri dolu |
| 2 | Integrity Check panelini kontrol et | Son snapshot hash, event count, seal status görünür |

#### TC-AUDIT-005: Derived Snapshot (Fallback)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bundle yokken ama kayıt varken kontrol et | Lokal derived audit snapshot otomatik oluşturulur |
| 2 | Derived snapshot'ın hash'ini kontrol et | Kayıt hash'lerinden üretilmiş birleşik hash |

---

## 5. Axiology

### 📌 Sayfanın Amacı
Etik/değer uyum denetim panosu. Aksiyoloji değerlendirme kayıtlarını kararlarıyla (approve/flag/reject) birlikte listeler. Güvenlik, risk ve kaynak bütünlüğü skorlarını Progress bar ile gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Scale ikonu + aktif durum göstergesi | Header | |
| 2 | 4 İstatistik Kartı | Kart | Alignment Score (98.4%), Risky Blocks (12), Audited Plans (842), Autonomous Fixes (45) |
| 3 | Ant Design Table | Tablo | Decision, Context, Justification, Scores, Time, Action sütunları |
| 4 | Decision Tag'leri | Tag | approve=yeşil, flag=uyarı, reject=hata |
| 5 | 3 Score Progress Bar | Progress | Safety %, Resources %, Risk % |
| 6 | Activity tooltip (hover) | Tooltip | Corrective action detayı |
| 7 | Eye detay linki | Link/İkon | `/axiology/{id}` detay sayfasına yönlendirir |
| 8 | Pagination + page size changer | Pagination | Sayfalama |

### ✅ Test Senaryoları

#### TC-AXIO-001: Tablo Görüntüleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/axiology` sayfasını aç | İstatistik kartları ve Ant Design tablosu yüklenir |
| 2 | İstatistik kartlarını kontrol et | Alignment Score: 98.4%, Risky Blocks: 12, Audited Plans: 842, Autonomous Fixes: 45 (veya güncel değerler) |
| 3 | Tablo sütunlarını kontrol et | Decision, Context, Justification, Scores, Time, Action mevcut |

#### TC-AXIO-002: Decision Tag'leri
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "approve" kararına sahip bir satırı bul | Tag yeşil renkte |
| 2 | "flag" kararına sahip bir satırı bul | Tag sarı/uyarı renkte |
| 3 | "reject" kararına sahip bir satırı bul | Tag kırmızı/hata renkte |

#### TC-AXIO-003: Score Progress Bar'lar
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Herhangi bir satırdaki Scores sütununu kontrol et | 3 progress bar mevcut: Safety %, Resources %, Risk % |
| 2 | Her progress bar'ın yüzdesini kontrol et | %0-100 arası mantıklı değerler |

#### TC-AXIO-004: Activity Tooltip ve Detay Linki
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir satırın Action sütunundaki Activity ikonunun üzerine gel | Corrective action metni tooltip olarak gösterilir |
| 2 | Eye ikonuna tıkla | `/axiology/{id}` detay sayfasına yönlendirilir |

#### TC-AXIO-005: Pagination
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Page size'ı 10'dan 20'ye değiştir | Tabloda 20 satır gösterilir |
| 2 | İkinci sayfaya geç | URL güncellenir, yeni veriler yüklenir |
| 3 | Sıralama başlığına tıkla | Tablo ilgili sütuna göre sıralanır |

---

## 6. BilgeAPI Ops

### 📌 Sayfanın Amacı
**Projenin en büyük sayfası (1930 satır!).** Tam teşekküllü BilgeAPI operasyon konsolu. 11 sekmeli admin panosu: API key yönetimi, araştırma, draft PR'lar, AI patch önerileri, governor bulguları, self-healing, değiştirilemez ledger, audit trail ve ajan yaşam döngüsü yönetimi.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | API key input (password field) | Input | Kimlik doğrulama |
| 2 | Refresh / Clear butonları | Buton | Veri yenileme / temizleme |
| 3 | 11 Sekme navigasyonu | Tab | Dashboard, API Keys, Research, Draft PRs, Revisions, AI Suggestions, Governor, Self-Healing, Ledger, Audit, Agents |
| 4 | Dashboard: 12 metrik kartı | Kart | API Keys, Active/Revoked, Quota, Release Gate, Research, PRs, vb. |
| 5 | Dashboard: Management Gate kilitle/aç | Toggle | Yönetim kapısı kontrolü |
| 6 | Dashboard: "Run Gate" butonu | Buton | Release readiness kontrolü |
| 7 | Keys: API Key oluştur formu | Form | Role, tenant, description, daily/monthly quotas |
| 8 | Keys: Pick / Revoke butonları | Buton | Anahtar seç / iptal et |
| 9 | Keys: Quota güncelle formu | Form | Günlük/aylık kota ayarları |
| 10 | Research: Araştırma talebi oluştur | Form | incident_id, query |
| 11 | Research: Proposal oluştur / onayla / gate / draft | Butonlar | Araştırma iş akışı |
| 12 | PRs: Context / Verify butonları | Buton | PR doğrulama |
| 13 | Revisions: Gözden geçiren geri bildirimi + yama | Form | Diff editörü ile |
| 14 | AI: Suggestion generate / verify / accept / reject | Butonlar | AI yama döngüsü |
| 15 | Governor: Acknowledge / Dismiss bulgu butonları | Buton | Bulgu yönetimi |
| 16 | Remediation: Trigger / Emergency Recovery | Form + Buton | Düzeltme tetikleme |
| 17 | Remediation: Runbook enable/disable | Toggle | Çalışma kitabı kontrolü |
| 18 | Ledger: Chain ID input + Load / Verify / Export | Form + Butonlar | Zincir doğrulama |
| 19 | Agents: Enable / Disable ajan | Toggle | Ajan kontrolü |
| 20 | Agents: Retry sandbox run | Buton | Sandbox yeniden çalıştırma |
| 21 | Agents: Promotion approve/reject/execute + simulation | Butonlar | Çok kapılı güvenlik onayı |

### ✅ Test Senaryoları

#### TC-BOPS-001: API Key ile Giriş ve Dashboard
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/bilgeapi-ops` sayfasını aç | Phase 27 badge ile header, API key input görünür |
| 2 | API key alanına geçerli bir key gir | Password field dolar |
| 3 | Refresh butonuna tıkla | `loadBilgeApiOpsSnapshot(apiKey)` çağrılır, 12 metrik kartı dolar |
| 4 | Dashboard sekmesindeki kartları kontrol et | Total API Keys, Active/Revoked, Quota Exceeded, Release Gate, vb. sayısal değerlerle dolu |

#### TC-BOPS-002: API Key Oluşturma (Keys Sekmesi)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "API Keys" sekmesine tıkla | Key oluşturma formu ve mevcut key'ler listesi görünür |
| 2 | Role: "operator" seç | Select dolar |
| 3 | Tenant: "production" gir | Input dolar |
| 4 | Description: "CI/CD pipeline key" gir | Input dolar |
| 5 | Daily quota: "1000" gir | Input dolar |
| 6 | Monthly quota: "25000" gir | Input dolar |
| 7 | "Create" butonuna tıkla | `createBilgeApiKey` çağrılır, yeni key listede görünür, quota bar'lar eklenir |

#### TC-BOPS-003: API Key İptal Etme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir key'in "Revoke" butonuna tıkla | Onay istenir |
| 2 | Onaylama | `revokeBilgeApiKey` çağrılır, key durumu "Revoked" olur |
| 3 | Dashboard'daki "Revoked" metrik kartını kontrol et | Sayı 1 artmış olmalı |

#### TC-BOPS-004: Araştırma İş Akışı (Research Sekmesi)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Research" sekmesine tıkla | Araştırma formu görünür |
| 2 | Incident ID: "INC-042" gir | Input dolar |
| 3 | Query: "API gateway 503 hatası root cause analizi" gir | Input dolar |
| 4 | "Create Research" tıkla | `createResearchRequest` çağrılır, araştırma oluşturulur |
| 5 | "Create Proposal" tıkla | Araştırma sonuçlarından proposal oluşturulur |
| 6 | "Approve" tıkla | Proposal onaylanır |
| 7 | "Run Gate" tıkla | Gate kontrolü çalıştırılır |
| 8 | "Draft PR" tıkla | Draft PR oluşturulur |
| 9 | "View Audit Report" tıkla | Denetim raporu görüntülenir |

#### TC-BOPS-005: AI Patch Suggestion Döngüsü
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "AI Suggestions" sekmesine tıkla | AI patch önerileri paneli görünür |
| 2 | "Generate Suggestion" tıkla | `createAiPatchSuggestion` çağrılır, yeni AI patch önerisi oluşturulur |
| 3 | Kod önizlemesini kontrol et | Önerilen patch kod bloğu olarak gösterilir |
| 4 | "Verify" tıkla | `verifyAiPatchSuggestion` çağrılır |
| 5 | "Accept for Review" tıkla | Öneri review kuyruğuna alınır |
| 6 | VEYA "Reject" tıkla | Öneri reddedilir |

#### TC-BOPS-006: Governor Watchdog (Governor Sekmesi)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Governor" sekmesine tıkla | 3 metrik kartı + findings tablosu + forbidden actions + governance audit summary görünür |
| 2 | Bir bulgunun "Acknowledge" butonuna tıkla | `acknowledgeFinding` çağrılır, bulgu "acknowledged" olarak işaretlenir |
| 3 | Bir bulgunun "Dismiss" butonuna tıkla | `dismissFinding` çağrılır |

#### TC-BOPS-007: Self-Healing Remediation
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Self-Healing" sekmesine tıkla | Remediation formu, runbook tablosu, geçmiş görünür |
| 2 | Finding ID: "F-001" gir | Input dolar |
| 3 | Runbook seç: "database-reconnect" | Select dolar |
| 4 | "Trigger Remediation" tıkla | `triggerRemediation` çağrılır |
| 5 | Runbook tablosunda bir runbook'u "Disable" tıkla | Runbook devre dışı bırakılır |
| 6 | "Emergency Recovery" formunu doldur ve tıkla | `runEmergencyRecovery` çağrılır |

#### TC-BOPS-008: Ledger Doğrulama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Ledger" sekmesine tıkla | Chain ID input, Load/Verify/Export butonları görünür |
| 2 | Chain ID gir ve "Load" tıkla | `getReviewLedgerChain` çağrılır, ledger girdileri listelenir |
| 3 | "Verify" tıkla | `verifyReviewLedgerChain` çağrılır, doğrulama sonucu gösterilir |
| 4 | "Export" tıkla | `exportReviewLedgerChain` çağrılır, export preview gösterilir |

#### TC-BOPS-009: Ajan Promotion (Agents Sekmesi)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Agents" sekmesine tıkla | Ajan yetenekleri listesi, sandbox run'lar, promotion talepleri görünür |
| 2 | Bir ajanı "Enable" et | `enableAgent` çağrılır |
| 3 | Bir sandbox run'da "Retry" tıkla | `retryAgentRun` çağrılır |
| 4 | Promotion detay panelini aç | Governance dry-run simülasyonu dahil detaylar |
| 5 | "Simulate" tıkla | `simulateAgentPromotion` çağrılır, simülasyon sonucu gösterilir |
| 6 | "Approve" tıkla | `approveAgentPromotion` çağrılır (çok kapılı güvenlik onayı) |
| 7 | "Execute Promotion" tıkla | `executeAgentPromotion` çağrılır |

#### TC-BOPS-010: Management Gate
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Dashboard sekmesinde Management Gate panelini bul | Lock/Unlock toggle mevcut |
| 2 | Gate'i "Lock" konumuna getir | `setManagementGate` çağrılır |
| 3 | Gate'i "Unlock" konumuna getir | Gate açılır, belirli işlemler etkinleşir |

---

## 7. Calibrations

### 📌 Sayfanın Amacı
Governor parametresi kalibrasyon yönetimi. Önerilen parametre değişikliklerini (proposed value changes) görüntüler. Approve/Reject/Rollback işlemleri Popconfirm ile onay gerektirir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ExperimentOutlined ikonu + header | Header | |
| 2 | "Scan for Calibration Proposals" butonu | Buton | Yeni kalibrasyon önerileri tarar |
| 3 | Açıklama kartı | Kart | Özellik açıklaması |
| 4 | Ant Design Table | Tablo | Parameter Name, Change, Confidence, Status, Reason, Created, Actions |
| 5 | Change sütunu | Hücre | Eski değer ~~üstü çizili~~ → yeni değer + renk kodlaması |
| 6 | Confidence Progress bar | Progress | Mor renk |
| 7 | Status Tag'leri | Tag | PROPOSED=mavi, APPLIED=yeşil, REJECTED=kırmızı, ROLLED_BACK=turuncu |
| 8 | Approve butonu (Popconfirm) | Buton | PROPOSED durumundakiler için |
| 9 | Reject butonu (Popconfirm) | Buton | PROPOSED durumundakiler için |
| 10 | Rollback butonu (Popconfirm) | Buton | APPLIED durumundakiler için |

### ✅ Test Senaryoları

#### TC-CALIB-001: Kalibrasyon Tablosu
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/calibrations` sayfasını aç | Header ve açıklama kartı ile tablo yüklenir |
| 2 | Tablo sütunlarını kontrol et | Parameter Name (cyan), Change, Confidence, Status, Reason, Created At, Actions mevcut |
| 3 | Change sütunundaki bir satırı kontrol et | Eski değer ~~üstü çizili~~, yeni değer renkli (iyileşme=yeşil, kötüleşme=kırmızı) + diff gösterilmeli |
| 4 | Created At formatını kontrol et | Türkçe göreceli zaman (ör. "10 dk önce") dayjs ile |

#### TC-CALIB-002: Kalibrasyon Onaylama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | PROPOSED durumlu bir satırın "Approve" butonuna tıkla | Popconfirm açılır: "Bu kalibrasyonu onaylamak istiyor musunuz?" |
| 2 | Popconfirm'da "Evet" tıkla | `POST /governance/governor/calibrations/{id}/approve` çağrılır |
| 3 | Satırın Status Tag'ini kontrol et | "APPLIED" (yeşil) olarak güncellenmeli |

#### TC-CALIB-003: Kalibrasyon Reddetme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | PROPOSED durumlu bir satırın "Reject" butonuna tıkla | Popconfirm açılır |
| 2 | "Evet" tıkla | `POST /governance/governor/calibrations/{id}/reject` çağrılır |
| 3 | Status: "REJECTED" (kırmızı) | Tag güncellenmeli |

#### TC-CALIB-004: Geri Alma (Rollback)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | APPLIED durumlu bir satırın "Rollback" butonuna tıkla | Popconfirm açılır |
| 2 | "Evet" tıkla | `POST /governance/governor/calibrations/{id}/rollback` çağrılır |
| 3 | Status: "ROLLED_BACK" (turuncu) | Tag güncellenmeli |

#### TC-CALIB-005: Yeni Öneri Taraması
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Scan for Calibration Proposals" butonuna tıkla | `POST /governance/governor/calibrations/propose` çağrılır |
| 2 | Tarama tamamlanır | Yeni PROPOSED satırlar tabloya eklenir |

---

## 8. Compliance

### 📌 Sayfanın Amacı
Veri uyumluluk politikası görüntüleyici ve mühürlenmiş denetim paketi yöneticisi. Saklama politikalarını ve düzenleyici uyumluluk için mühürlenmiş kanıt paketlerini gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + bütünlük hash (99.99% Nominal) | Header | |
| 2 | "New Bundle" butonu | Buton | Denetim paketi oluşturma modal açar |
| 3 | Active Policies listesi (sol sütun) | Liste | Data category, permanent badge, hot/cold storage days |
| 4 | Parity Monitor (sol sütun) | Panel | 99.99% bütünlük, baseline, sealing göstergesi |
| 5 | Sealed Evidence tablosu (sağ sütun) | Tablo | Bundle Name, Purpose, Integrity Seal (hash), Actions |
| 6 | Arama input (tablo üstü) | Input | Paket araması |
| 7 | Filtre butonu | Buton | Filtreleme (stub) |
| 8 | Download / Eye butonları (hover ile görünür) | Buton | Paket indirme / görüntüleme |
| 9 | Create Audit Bundle modal | Modal | Name input, purpose textarea, Cancel/Seal butonları |

### ✅ Test Senaryoları

#### TC-COMP-001: Uyumluluk Politikalarını Görüntüleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/compliance` sayfasını aç | Sol sütunda politikalar, sağ sütunda mühürlenmiş paketler görünür |
| 2 | Active Policies listesini kontrol et | Her politikada: data category, "permanent" badge, hot storage days, cold retention days bilgileri |
| 3 | Parity Monitor'ü kontrol et | "99.99%" bütünlük yüzdesi, integrity baseline, sealing active göstergesi |

#### TC-COMP-002: Mühürlenmiş Kanıt Paketi Oluşturma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "New Bundle" butonuna tıkla | Create Audit Bundle modal açılır |
| 2 | Name: "Q2-2026-KVKK-Audit" gir | Input dolar |
| 3 | Purpose: "2026 Q2 KVKK uyumluluk denetimi kanıt paketi" gir | Textarea dolar |
| 4 | "Seal" butonuna tıkla | `POST /api/v1/governance/compliance/audit-bundles` çağrılır, modal kapanır, paket tabloya eklenir |
| 5 | "Cancel" tıkla (iptal testi) | Modal kapanır, paket oluşturulmaz |

#### TC-COMP-003: Sealed Evidence Tablosu
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Tabloyu kontrol et | Bundle Name (tarih ile), Purpose, Integrity Seal (kırpılmış hash), Actions sütunları mevcut |
| 2 | Bir satırın üzerine gel (hover) | Download ve Eye butonları görünür |
| 3 | Download butonuna tıkla | İndirme işlemi başlar (placeholder) |
| 4 | Eye butonuna tıkla | Paket detayı görüntülenir (placeholder) |

#### TC-COMP-004: Arama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Arama alanına "KVKK" yaz | Sadece adında "KVKK" geçen paketler filtrelenir |
| 2 | Arama alanını temizle | Tüm paketler geri döner |

---

## 9. Costs

### 📌 Sayfanın Amacı
Finansal/maliyet analiz panosu. Bütçe tüketimi, yanma oranları (burn rates), proje bazlı ekonomi ve otonom optimizasyon önerileri gösterir. Runway (kalan gün) göstergesi içerir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + Wallet ikonu + "Runway" göstergesi | Header | Kalan gün sayısı |
| 2 | "Adjust Guardrails" butonu | Buton | Korkuluk ayarları (stub) |
| 3 | Total Consumption kartı | Kart | $ + usage % progress bar + limit |
| 4 | Fleet Burn Rate kartı | Kart | $/saat |
| 5 | Scale Efficiency kartı | Kart | 98.1% |
| 6 | Guardrails Status kartı | Kart | Kilit ikonu, "Policy Engaged" |
| 7 | Spend Units / Proje Ekonomisi listesi (sol) | Liste | Proje kartları: title, node ID, burn rate (renkli), budget remaining + progress bar |
| 8 | Density Radar (sağ) | Liste | En yüksek maliyetli projeler sıralaması |
| 9 | Tactical Economics optimizasyon kartı (sağ) | Kart | Tasarruf önerisi + "Apply Optimization" butonu + güven skoru |

### ✅ Test Senaryoları

#### TC-COST-001: Maliyet Genel Bakış
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/costs` sayfasını aç | ResourceHeader'da Runway göstergesi ("X gün kaldı") görünür |
| 2 | 4 overview kartı kontrol et | Total Consumption ($ + % + limit), Fleet Burn Rate ($/hr), Scale Efficiency (%), Guardrails Status |
| 3 | Total Consumption progress bar'ını kontrol et | Kullanım yüzdesi görsel olarak gösterilmeli |

#### TC-COST-002: Proje Bazlı Ekonomi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sol sütundaki Spend Units listesini kontrol et | Her projede: title, node ID, hourly burn rate, budget remaining |
| 2 | Burn rate renklerini kontrol et | Yüksek burn rate = kırmızı/turuncu, düşük = yeşil |
| 3 | Budget remaining progress bar'ını kontrol et | Kalan bütçe yüzdesi görsel olarak |

#### TC-COST-003: Density Radar
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sağ sütundaki Density Radar'ı kontrol et | En yüksek maliyetli projeler $ tutarıyla sıralı listelenmeli |
| 2 | Expand butonuna tıkla | Tam liste açılır (stub) |

#### TC-COST-004: Optimizasyon Önerisi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Tactical Economics kartını kontrol et | Optimizasyon önerisi: ne kadar tasarruf, nerede, nasıl |
| 2 | Karar güvenini kontrol et | Ör. "94.2%" güven skoru |
| 3 | "Apply Optimization" butonuna tıkla | (Stub — henüz işlevsel değil) |

---

## 10. Evolution

### 📌 Sayfanın Amacı
Sistem oto-evrim defteri. AGI sisteminin kendisine yaptığı otonom kod değişikliklerini/güncellemelerini gösterir: diff'ler, test sonuçları, git commit'leri. **Her 30 saniyede otomatik yenilenir.**

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + DNA ikonu + versiyon + son sync zamanı | Header | |
| 2 | Refresh butonu | Buton | Manuel yenileme |
| 3 | Update Stream Timeline (sol sütun) | Timeline | Dikey zaman çizelgesi: timestamp, status, description, target file |
| 4 | Detay Görünümü (sağ sütun) | Panel | Seçilen güncellemenin detayları |
| 5 | Git commit hash | Text | Commit referansı |
| 6 | 3 Detay Metriği | Kart | Target File, Execution ID, Validation |
| 7 | Change Summary | Panel | Diff önizlemesi + değişen sembol badge'leri |
| 8 | Self-Test Report | Panel | Syntax Check, Logical Consistency, Safety Constraints |
| 9 | "Evolutionary Jump" vurgu kartı | Kart | "View Code Lineage" linki |
| 10 | Error banner | Alert | Bağlantı sorunları için |

### ✅ Test Senaryoları

#### TC-EVOL-001: Timeline Görüntüleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/evolution` sayfasını aç | DNA ikonu, versiyon (ör. v12.1), son sync zamanı ile header yüklenir |
| 2 | Sol sütundaki timeline'ı kontrol et | Dikey zaman çizelgesi: her öğede timestamp, status (applied/pending), description, target file |
| 3 | Timeline noktaları kronolojik sırada mı kontrol et | En yeni en üstte |

#### TC-EVOL-002: Güncelleme Detayı Görüntüleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Timeline'daki bir öğeye tıkla | Sağ sütunda detay paneli yüklenir |
| 2 | Description ve rationale'i kontrol et | Anlamlı metin mevcut |
| 3 | Git commit hash'i kontrol et | Geçerli commit hash formatı |
| 4 | 3 detay metriğini kontrol et | Target File (dosya yolu), Execution ID, Validation (PASSED/SHADOW RUNNER) |

#### TC-EVOL-003: Change Summary ve Self-Test
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Change Summary panelini kontrol et | Diff önizlemesi + değişen sembol badge'leri görünür |
| 2 | Self-Test Report'u kontrol et | Syntax Check: PASSED, Logical Consistency: VERIFIED, Safety Constraints: ENFORCED |

#### TC-EVOL-004: Otomatik Yenileme (30 saniye)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sayfayı aç ve 60 saniye bekle | En az 1 kez otomatik veri yenilenmesi (network sekmesinde doğrulanabilir) |

#### TC-EVOL-005: Error Banner ve Fallback
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | API bağlantısı kesildiğinde kontrol et | Error banner gösterilir: bağlantı durumu ve operator notu |
| 2 | Fallback endpoint'i çağrılıyor mu kontrol et | `GET /api/v1/health/evolution?limit=20` çağrılır |

---

## 11. Federation

### 📌 Sayfanın Amacı
Çok bölgeli federasyon kümesi monitörü. Ajan kümeleri, arbitrasyon kararları ve bölgesel durumları gösterir. **Tamamen hardcoded/mock veri kullanır — API çağrısı yoktur.**

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + global quorum (5/5 Active) | Header | |
| 2 | "Matrisi Dışa Aktar" butonu | Buton | Export (stub) |
| 3 | 4 Küme Kartı (seçilebilir) | Kart | Güvenlik Kümesi (US-EAST), Alan Mantığı (EU-CENTRAL), Altyapı (AP-SOUTH), Maliyet (US-WEST) |
| 4 | Trust % + Load % progress bar | Progress | Her kümede |
| 5 | Arbitration Log (sol 8/12) | Kart listesi | Target file, winner cluster, reasoning, hash, complexity |
| 6 | Regional Status heatmap (sağ 4/12) | Bar | Logic Synapse 88%, Security Gate 94%, Economic Steering 42%, Infra 76% |
| 7 | Global Sync gecikme göstergesi | Text | 92ms |
| 8 | Protocols bölümü | Liste | Konsensüs kuralları |
| 9 | "Full Protocol Specs" butonu | Buton | (Stub) |

### ✅ Test Senaryoları

#### TC-FED-001: Küme Kartları
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/federation` sayfasını aç | 4 küme kartı ve arbitrasyon logu görünür |
| 2 | Her küme kartını kontrol et | Ad, bölge, trust %, load %, status bilgileri dolu |
| 3 | "Güvenlik Kümesi" kartını kontrol et | US-EAST, trust 98%, load 12% |
| 4 | "Maliyet Ekonomisi" kartını kontrol et | US-WEST, trust 99%, load 2% |

#### TC-FED-002: Küme Seçimi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Alan Mantığı" kartına tıkla | Kart seçili/vurgulanmış duruma geçer |
| 2 | Başka bir karta tıkla | Önceki seçim kalkar, yeni kart seçilir |

#### TC-FED-003: Arbitration Log
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Arbitrasyon logunu kontrol et | Çatışma/konsensüs çözümleri kartları mevcut |
| 2 | Her kartın içeriğini kontrol et | Target file, winner cluster, reasoning, hash, complexity level |

#### TC-FED-004: Regional Status Heatmap
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sağ sidebar'daki heatmap bar'larını kontrol et | Logic Synapse 88%, Security Gate 94%, Economic Steering 42%, Infra 76% |
| 2 | Global Sync değerini kontrol et | "92ms" gecikme |

---

## 12. Fleet

### 📌 Sayfanın Amacı
Çok ajanlı filo orkestrasyon panosu. Ajanların, kümelerin ve filo olaylarının gerçek zamanlı izlenmesi. Renk kodlu canlı olay akışı.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | 5 İstatistik Kartı | Kart | Active Agents, Queued Projects, Busy Ratio (progress bar), Budget ($USD), Quarantined (kırmızı >0) |
| 2 | Cluster Status tablosu (sol) | Ant Table | Cluster Name, Status Tag, Load Progress, Agent Count, Budget Usage % |
| 3 | "Manage Clusters" butonu | Buton | (Stub) |
| 4 | Recent Fleet Events (sağ) | Kart scroll | Canlı olay akışı renk kodlu sol kenarlık |
| 5 | Olay türü Tag'leri | Tag | AGENT_ASSIGNED=yeşil, BUDGET_BLOCK=turuncu, QUARANTINED=kırmızı, CLUSTER_FROZEN=cyan, RELEASED=mavi, REBALANCED=mor |

### ✅ Test Senaryoları

#### TC-FLEET-001: Filo Metrikleri
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/fleet` sayfasını aç | 5 istatistik kartı + cluster tablosu + olay akışı yüklenir |
| 2 | Active Agents kartını kontrol et | Pozitif tam sayı |
| 3 | Busy Ratio kartını kontrol et | Progress bar ile yüzde gösterilir |
| 4 | Budget kartını kontrol et | USD formatında maliyet |
| 5 | Quarantined Agents kartını kontrol et | 0 ise normal, >0 ise kırmızı kenarlık |

#### TC-FLEET-002: Cluster Status Tablosu
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Cluster tablosunu kontrol et | Cluster Name, Status (ACTIVE=yeşil tag), Load (progress), Agent Count, Budget % |
| 2 | En az 1 cluster "ACTIVE" durumda | Yeşil tag ile |

#### TC-FLEET-003: Canlı Olay Akışı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Recent Fleet Events panelini kontrol et | Renk kodlu sol kenarlıklarla olaylar listelenir |
| 2 | AGENT_ASSIGNED olayını kontrol et | Yeşil kenarlık + yeşil tag |
| 3 | BUDGET_BLOCK olayını kontrol et (varsa) | Turuncu kenarlık + turuncu tag |
| 4 | AGENT_QUARANTINED olayını kontrol et (varsa) | Kırmızı kenarlık + kırmızı tag |
| 5 | Her olayın timestamp ve payload özetini kontrol et | Okunabilir formatta mevcut |

---

## 13. Governor

### 📌 Sayfanın Amacı
Governor gelen kutusu — AI yönetişim vaka yönetimi. Risk puanlaması, önerilen kararlar ve toplu işlemler (approve/replay/archive) ile yönetişim vakalarını listeler. Checkbox ile çoklu seçim destekler.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | SafetyOutlined ikonu + header | Header | |
| 2 | "Approve Selected" butonu | Buton | Seçili vakaları toplu onayla |
| 3 | "Replay Selected" butonu | Buton | Seçili vakaları yeniden oynat |
| 4 | "Archive Selected" butonu | Buton | Seçili vakaları arşivle |
| 5 | "Refresh" butonu | Buton | Veri yenileme |
| 6 | 4 Özet İstatistik Kartı | Kart | Open Alerts (kırmızı), Active Drifts (turuncu, dönen ikon), Last Breach, Accuracy 1h |
| 7 | Ant Table (checkbox'lu) | Tablo | Project/Action, Risk/Score, Wait Reason, Decision Summary, Context, Actions |
| 8 | Row selection checkbox'ları | Checkbox | Toplu işlem için satır seçimi |
| 9 | Risk/Score Tag'leri | Tag | LOW=yeşil, MEDIUM=turuncu, HIGH=volcano, CRITICAL=kırmızı + sayısal skor |
| 10 | Decision Summary | Badge | APPLIED/RECOMMENDATION + reason codes |
| 11 | Context ikonları | İkon | Open incident uyarısı, prime approval gerekli, çok eski (stale) |
| 12 | "Review" butonu | Buton | Vaka detay sayfasına yönlendirir |

### ✅ Test Senaryoları

#### TC-GOVR-001: Governor Vaka Listesi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor` sayfasını aç | 4 özet kartı + checkbox'lu Ant Table yüklenir |
| 2 | Open Alerts kartını kontrol et | Kırmızı kenarlıklı, sayısal değer |
| 3 | Active Drifts kartını kontrol et | Turuncu kenarlıklı, dönen ikon |
| 4 | Accuracy 1h kartını kontrol et | Yeşil, yüzde formatında (ör. 96.4%) |

#### TC-GOVR-002: Risk Tag'leri
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Risk/Score sütununu kontrol et | Her satırda renk kodlu risk tag'i + sayısal skor |
| 2 | CRITICAL risk tag'ini bul | Kırmızı renkte |
| 3 | LOW risk tag'ini bul | Yeşil renkte |

#### TC-GOVR-003: Toplu Onaylama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | 3 satırın checkbox'ını işaretle | 3 satır seçili duruma geçer |
| 2 | "Approve Selected" butonuna tıkla | `POST /governance/governor/cases/{id}/override` çağrılır (her biri için), reason: approve |
| 3 | Seçili satırların durumlarını kontrol et | Tümü güncellenmeli |

#### TC-GOVR-004: Toplu Arşivleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | 2 satırı seç | Checkbox'lar işaretli |
| 2 | "Archive Selected" tıkla | Override API çağrılır, reason: archive |
| 3 | Satırlar arşivlenir | Listeden kaybolur veya durumları güncellenir |

#### TC-GOVR-005: Tekil Vaka İnceleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir satırın "Review" butonuna tıkla | Vaka detay sayfasına yönlendirilir |

#### TC-GOVR-006: Context İkonları
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Açık olay uyarı ikonu olan satırı bul | Uyarı ikonu görünür |
| 2 | "Prime approval required" ikonu olan satırı bul | İlgili ikon mevcut |
| 3 | "Very stale" ikonu olan satırı bul | Eski vaka göstergesi |

---

## 14. Identity

### 📌 Sayfanın Amacı
Ajan kimliği ve API Key yöneticisi. SIF-02/SIF-04 standardına uygun güven puanlaması, karantina kontrolleri ve API key oluşturma/rotasyon sağlar.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + "SIF-02 Standard" badge | Header | |
| 2 | Kimlik kartları grid'i (1-3 sütun) | Kart grid | Fingerprint ikonu, ad, UUID, risk level badge, trust score progress bar, last-used |
| 3 | Risk level badge'leri | Badge | LOW=yeşil, MEDIUM=sarı, HIGH=kırmızı |
| 4 | Trust score progress bar | Progress | Her kartta |
| 5 | Karantina overlay (kilit ikonu) | Overlay | Karantinalı kimliklerde |
| 6 | "New Identity" butonu | Buton | ADMIN/SOVEREIGN_PRIME rolü gerektirir (yoksa disabled) |
| 7 | "Rotate" butonu | Buton | API key rotasyonu |
| 8 | Kalkan butonu (quarantine) | Buton | Ajanı karantinaya alır (onay dialog) |
| 9 | Yenile butonu (recover) | Buton | Karantinalı ajanı kurtarır (onay dialog) |
| 10 | Key Discovery Modal | Modal | Yeni oluşturulan API key + panoya kopyala |

### ✅ Test Senaryoları

#### TC-ID-001: Kimlik Kartları
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/identity` sayfasını aç | "SIF-02 Standard" badge ile kimlik kartları grid'i yüklenir |
| 2 | Her kartın içeriğini kontrol et | Fingerprint ikonu, ad, UUID, risk level badge (LOW/MEDIUM/HIGH), trust score progress bar, last-used timestamp |
| 3 | Risk level renklerini kontrol et | LOW=yeşil, MEDIUM=sarı, HIGH=kırmızı |

#### TC-ID-002: API Key Rotasyonu
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir kimlik kartındaki "Rotate" butonuna tıkla | `POST /api/v1/auth/identity/keys/generate?target_id={id}` çağrılır |
| 2 | Key Discovery Modal açılır | Yeni oluşturulan API key gösterilir |
| 3 | Kopyala butonuna tıkla | Key panoya kopyalanır, "Kopyalandı" toast mesajı |
| 4 | Modalı kapat | Normal görünüme dönülür |

#### TC-ID-003: Ajan Karantinaya Alma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir kartın kalkan butonuna tıkla | Onay dialogu açılır |
| 2 | Onaylama | `POST /api/v1/auth/identity/{id}/quarantine` çağrılır |
| 3 | Kartı kontrol et | Karantina overlay (kilit ikonu) eklenir |

#### TC-ID-004: Karantinadan Kurtarma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Karantinalı bir kartın yenile butonuna tıkla | Onay dialogu açılır |
| 2 | Onaylama | `POST /api/v1/auth/identity/{id}/recover` çağrılır |
| 3 | Karantina overlay kalkar | Kart normal duruma döner |

#### TC-ID-005: Yetki Kontrolü
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | ADMIN olmayan kullanıcı ile giriş yap | "New Identity" butonu disabled durumda |
| 2 | ADMIN kullanıcı ile giriş yap | "New Identity" butonu aktif |

---

## 15. Improvements

### 📌 Sayfanın Amacı
AI tarafından önerilen kod iyileştirmelerini/patch'lerini gösterir. Operatörler önerilen sentetik yamaları inceleyebilir, onaylayabilir veya reddedebilir. Otonom kod onarımı için yönetişim kapısı.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + "Recalibrate" butonu | Header | |
| 2 | 3 Metrik Kartı | Kart | Pending Approval, Total Healed, Integrity (94%) |
| 3 | Arama input | Input | Dosya adı/talimat ile arama |
| 4 | Filtre dropdown | Select | all / pending / approved / applied / rejected / failed |
| 5 | İyileştirme öğe kartları | Kart | Target file, instruction, status badge, proposed patch (`<pre>` kod bloğu) |
| 6 | Doğrulayıcı badge'leri | Badge | Syntax PASSED, Unit Tests 12/12, Consensus VERIFIED |
| 7 | "Approve & Apply" butonu | Buton | Sadece pending öğeler |
| 8 | "Reject Patch" butonu | Buton | Sadece pending öğeler |
| 9 | "View Diffs" butonu | Buton | (Stub — handler yok) |

### ✅ Test Senaryoları

#### TC-IMP-001: İyileştirme Listesi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/improvements` sayfasını aç | 3 metrik kartı + iyileştirme kartları yüklenir |
| 2 | Metrik kartlarını kontrol et | Pending Approval (sayı), Total Healed (sayı), Integrity (%) |
| 3 | Bir iyileştirme kartını kontrol et | Target file, instruction, status badge, proposed patch (kod bloğu), doğrulayıcı badge'leri |

#### TC-IMP-002: Patch Onaylama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Pending durumlu bir kartın "Approve & Apply" butonuna tıkla | `PATCH governance/improvements/{id}` çağrılır, `{status: "approved"}` |
| 2 | Kartın durumunu kontrol et | Status badge "approved" olarak güncellenir |
| 3 | "Pending Approval" metrik kartını kontrol et | Sayı 1 azalmış olmalı |

#### TC-IMP-003: Patch Reddetme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Pending durumlu bir kartın "Reject Patch" butonuna tıkla | `PATCH governance/improvements/{id}` çağrılır, `{status: "rejected"}` |
| 2 | Status badge "rejected" olarak güncellenir | Kart kırmızı badge gösterir |

#### TC-IMP-004: Arama ve Filtreleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Arama alanına "auth.py" yaz | Sadece auth.py ile ilgili iyileştirmeler görünür |
| 2 | Filtre dropdown'dan "approved" seç | Sadece onaylanmış iyileştirmeler görünür |
| 3 | Filtre'yi "all" yapın, aramayı temizle | Tüm iyileştirmeler geri döner |

---

## 16. Incidents

### 📌 Sayfanın Amacı
Gerçek zamanlı olay izleme ve çözüm panosu. Severity seviyelerine göre renk kodlanmış olayları gösterir. Tek tek veya toplu çözüm sağlar. "Chaos Protocol" butonu ve otonom iyileşme başarı oranı gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + "Global Pulse" durum göstergesi | Header | |
| 2 | "Chaos Protocol" butonu | Buton | |
| 3 | İki sütunlu layout (8:4) | Layout | Sol: olay akışı, Sağ: sidebar |
| 4 | Olay akışı arama input | Input | (Mevcit ama state'e bağlı değil) |
| 5 | Filter butonu | Buton | |
| 6 | Olay kartları (kaydırılabilir, max 800px) | Kart | Type, status badge, severity (critical=kırmızı+alev ikonu, animasyonlu), message, suggested fix, diagnosis, timestamp, project/node ID |
| 7 | Suggested fix kopyala butonu | Buton | Komut panoya kopyalanır |
| 8 | "Take Action" butonu | Buton | Tek olayı çözer |
| 9 | Severity Monitor (sağ bar) | Gauge | Critical/High/Medium çubukları |
| 10 | Mitigation HUD (sağ bar) | Panel | %92 otonom iyileşme başarısı |
| 11 | "Clear All" butonu (sağ bar) | Buton | Tüm çözümlenmemiş olayları toplu çözer |
| 12 | Error durumu + Retry butonu | Alert + Buton | Hata durumunda |

### ✅ Test Senaryoları

#### TC-INC-001: Olay Akışı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/incidents` sayfasını aç | "Global Pulse" göstergesi ile olay akışı ve sidebar yüklenir |
| 2 | Olay kartlarını kontrol et | Her kartta: type, status badge, severity (renkli), message, suggested fix, diagnosis, timestamp |
| 3 | Critical severity kartını kontrol et | Kırmızı arka plan, alev ikonu, animasyonlu |
| 4 | Suggested fix kod bloğunu kontrol et | `<pre>` içinde komut mevcut |

#### TC-INC-002: Tek Olay Çözümleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir olayın "Take Action" butonuna tıkla | `POST /governance/incidents/{id}/resolve` çağrılır (resolution notes ve operator ID ile) |
| 2 | Olay listesini kontrol et | Çözümlenen olay listeden kalkar veya durumu güncellenir |

#### TC-INC-003: Toplu Çözümleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sağ sidebar'daki "Clear All" butonuna tıkla | Tüm çözümlenmemiş olaylar için sırayla `resolve` API çağrılır |
| 2 | Olay listesi kontrol et | Tüm olaylar çözümlenmiş durumda |

#### TC-INC-004: Suggested Fix Kopyalama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir olayın suggested fix yanındaki kopyala butonuna tıkla | Komut panoya kopyalanır |
| 2 | Bir editöre yapıştır | Doğru komut yapıştırılır |

#### TC-INC-005: Severity Monitor
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sağ sidebar'daki Severity Monitor gauge'lerini kontrol et | Critical, High, Medium çubukları mevcut |
| 2 | Mitigation HUD'u kontrol et | "%92 otonom iyileşme başarısı" veya benzeri değer |

---

## 17. MCP Hub

### 📌 Sayfanın Amacı
MCP (Model Context Protocol) sunucu yapılandırma merkezi. Kayıtlı MCP sunucularını türleriyle (stdio/sse/http), durumlarıyla ve bağlantı bilgileriyle gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Boxes ikonu + header | Header | |
| 2 | Refresh butonu (fetch sırasında dönen animasyon) | Buton | |
| 3 | 3 İstatistik Kartı | Kart | Total Servers, Active Nodes, Security Layer (V18.2) |
| 4 | Server kart grid'i (1-2 sütun) | Kart grid | Ad, type badge (stdio/sse/http), enabled/disabled status, description, entry command (stdio) / endpoint URL (http/sse), chevron butonu |
| 5 | Type badge'leri | Badge | stdio/sse/http |
| 6 | Enabled/Disabled status badge | Badge | |
| 7 | Chevron navigasyon butonu | Buton | (Handler bağlı değil) |

### ✅ Test Senaryoları

#### TC-MCP-001: Sunucu Listesi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/mcp-hub` sayfasını aç | 3 istatistik kartı + sunucu grid'i yüklenir |
| 2 | Total Servers kartını kontrol et | Grid'deki sunucu sayısıyla eşleşmeli |
| 3 | Her sunucu kartını kontrol et | Ad, type badge, status badge, description mevcut |

#### TC-MCP-002: Sunucu Türleri
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "stdio" türünde bir sunucu bul | Entry command (komut) gösterilmeli |
| 2 | "http" veya "sse" türünde bir sunucu bul | Endpoint URL gösterilmeli |

#### TC-MCP-003: Refresh
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Refresh butonuna tıkla | Buton dönen animasyon gösterir |
| 2 | `GET /api/v1/mcp/config` çağrılır | Veri yeniden yüklenir |
| 3 | Animasyon durur | Normal buton durumuna döner |

#### TC-MCP-004: Boş Durum
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Hiç sunucu yapılandırılmamışsa kontrol et | Empty state mesajı gösterilir |

---

## 18. Meeting Room

### 📌 Sayfanın Amacı
Çok ajanlı tartışma ve konsensüs odası. **WebSocket ile gerçek zamanlı streaming.** AI uzman ajanları mimari/politika önerileri üzerinde tartışır ve oy kullanır. Canlı düşünce ve oy akışı.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + sekmeler (Setup / Archive) | Header | |
| 2 | Proposal textarea | Textarea | Öneri metni girişi |
| 3 | 3 Şablon butonu | Buton | Önceden doldurulmuş öneri şablonları |
| 4 | Konsensüs uyarı notice | Notice | |
| 5 | "Start Meeting" butonu | Buton | WebSocket bağlantısı başlatır |
| 6 | Loading spinner | Spinner | Ajan toplanırken |
| 7 | Debate mesaj timeline | Timeline | Ajan emoji, ad, rol, düşünce alıntısı, aktif konuşmacı göstergesi |
| 8 | Voting kartları grid'i (3 sütun) | Kart grid | Approve/reject + gerekçe |
| 9 | "Stop Meeting" butonu | Buton | WebSocket bağlantısını keser |
| 10 | "New Discussion" butonu | Buton | Sıfırlar |
| 11 | Katılımcı seçici listesi (sağ) | Kart listesi | Checkbox'lu, emoji, ad, rol |
| 12 | Toplantı sonuç özeti | Panel | Konsensüs SAĞLANDI/REDDEDİLDİ, karar durumu, hüküm politikası |

### ✅ Test Senaryoları

#### TC-MEET-001: Toplantı Başlatma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/meeting-room` sayfasını aç | Proposal textarea, katılımcı listesi ve şablon butonları görünür |
| 2 | Katılımcı listesini kontrol et | `GET /debate/participants` çağrılır, uzman ajanlar listelenir |
| 3 | En az 2 katılımcı seç (checkbox tıkla) | Seçilen ajanlar vurgulanır |
| 4 | Proposal textarea'ya yaz: "API Gateway önbellek stratejisi — Redis vs Memcached karşılaştırması" | Textarea dolar |
| 5 | "Start Meeting" butonuna tıkla | WebSocket bağlantısı `{wsBase}/debate/meeting` adresine açılır, proposal + participant_ids gönderilir |
| 6 | Loading spinner görünür | "Ajanlar toplanıyor..." mesajı |

#### TC-MEET-002: Şablon Butonları
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | 1. şablon butonuna tıkla | Textarea önceden tanımlı bir proposal metniyle dolar |
| 2 | 2. şablon butonuna tıkla | Farklı bir proposal metniyle dolar |

#### TC-MEET-003: Canlı Tartışma İzleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Toplantı başladıktan sonra debate timeline'ı izle | WebSocket `thought` olayları gelir: ajan emoji, ad, rol, düşünce alıntısı |
| 2 | Aktif konuşmacı göstergesini kontrol et | Konuşan ajanın kartı vurgulanır |
| 3 | Mesajlar kronolojik sırada | En yeni en altta |

#### TC-MEET-004: Oylama Sonuçları
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | WebSocket `vote` olayları geldiğinde kontrol et | Voting kartları grid'inde her ajan için approve/reject + gerekçe |
| 2 | Her oylama kartını kontrol et | Ajan adı, approve veya reject, neden |

#### TC-MEET-005: Toplantı Sonucu
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | WebSocket `complete` olayı geldiğinde kontrol et | Sonuç özeti paneli dolar |
| 2 | Konsensüs durumunu kontrol et | "Konsensüs SAĞLANDI" veya "Konsensüs REDDEDİLDİ" |
| 3 | Karar durumu ve hüküm politikasını kontrol et | Anlamlı metin |

#### TC-MEET-006: Toplantıyı Durdurma ve Yeni Tartışma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Stop Meeting" butonuna tıkla | WebSocket bağlantısı kesilir |
| 2 | "New Discussion" butonuna tıkla | Form ve timeline sıfırlanır, yeni toplantı hazır |

#### TC-MEET-007: Min 2 Katılımcı Kuralı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sadece 1 katılımcı seç | "Start Meeting" butonu devre dışı veya uyarı |
| 2 | 2. katılımcıyı seç | Buton aktif olur |

---

## 19. Mesh

### 📌 Sayfanın Amacı
Global yüksek erişilebilirlik kontrol mesh'i. Çok bölgeli altyapı izleme ve kriz orkestrasyonu. Bölge sağlığı, quorum konsensüsü, trafik müdahale kontrolleri ve drift politikası. **Her 5 saniyede otomatik polling.**

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + global sync latency (0.04ms) | Header | |
| 2 | Refresh butonu | Buton | Manuel yenileme |
| 3 | ChaosMap bileşeni (sol) | Görselleştirme | Bölge topoloji: Europe-North, Americas-East, Asia-Pacific (renkli sağlık) |
| 4 | FailoverTimeline bileşeni (sol) | Timeline | Mesh aktivite olay zaman çizelgesi |
| 5 | QuorumHealthPanel (sağ) | Panel | Total/healthy node sayıları, quorum maintained durumu |
| 6 | "Engage Security Override" toggle | Buton | Güvenlik override açar/kapatır |
| 7 | Reroute / Throttle kontrolleri | Buton | Override aktifken kullanılabilir |
| 8 | Lock overlay | Overlay | Override kapalıyken "Operator Authority" gerektirir |
| 9 | Drift Policy bölümü | Liste | Emergency Failover, Quorum Weights, Baseline Parity + baseline hash |
| 10 | OperatorConsole bileşeni | Bileşen | Quorum maintained olmadığında kilitli |

### ✅ Test Senaryoları

#### TC-MESH-001: Mesh Topolojisi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/mesh` sayfasını aç | ChaosMap ve QuorumHealthPanel yüklenir |
| 2 | Global sync latency'yi kontrol et | "0.04ms" veya benzeri düşük değer |
| 3 | ChaosMap bölge overlay'lerini kontrol et | Europe-North, Americas-East, Asia-Pacific bölge mini-istatistikleri (renkli sağlık) |
| 4 | QuorumHealthPanel'i kontrol et | Total nodes, healthy nodes, "Quorum Maintained" durumu |

#### TC-MESH-002: Security Override Toggle
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Traffic Hub bölümünü kontrol et | Lock overlay: "Operator Authority" gerektirir |
| 2 | "Engage Security Override" toggle'ına tıkla | Override aktif, lock overlay kalkar |
| 3 | Reroute butonuna tıkla | Trafik yeniden yönlendirme tetiklenir |
| 4 | Throttle butonuna tıkla | Trafik kısıtlama tetiklenir |
| 5 | "Deactivate Security Override" tıkla | Override kapanır, butonlar tekrar kilitlenir |

#### TC-MESH-003: Override Kapalıyken Kontroller
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Override kapalı iken Reroute butonuna tıklamayı dene | Buton devre dışı veya lock overlay tıklamayı engeller |

#### TC-MESH-004: Otomatik Polling (5 saniye)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sayfayı aç ve 15 saniye bekle | `GET /api/v1/mesh/status` ve `/mesh/timeline?limit=15` en az 2 kez çağrılır |

#### TC-MESH-005: Drift Policy
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Drift Policy bölümünü kontrol et | Emergency Failover, Quorum Weights, Baseline Parity öğeleri mevcut |
| 2 | Baseline hash'i kontrol et | Güvenlik notice ile geçerli hash gösterilir |

---

## 20. Policy Proposals

### 📌 Sayfanın Amacı
Anayasal yönetişim ve politika onay sistemi. Yasama önerileri (amendment'lar), sign-off onayı ve yeni değişiklik oluşturma. Konsensüs quorum takibi ve git lineage desteği.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | ResourceHeader + tüzük versiyonu (v9.4.2-STABLE) | Header | |
| 2 | "New Amendment" butonu | Buton | Yeni değişiklik modal açar |
| 3 | Arama input | Input | Öneri araması |
| 4 | Filter butonu | Buton | |
| 5 | Öneri kartları (sol) | Kart listesi | Kalkan ikonu, başlık, scope badge, tarih, status badge (COMMITTED/PROPOSED), konsensüs quorum progress bar, imzacılar listesi, git commit SHA |
| 6 | Amendment Detail paneli (sağ) | Panel | Anayasal etki açıklaması, amendment ID, yazar, "Kurumsal Sign-off Ver" butonu |
| 7 | "Kurumsal Sign-off Ver" butonu | Buton | PROPOSED olmayanlarda disabled |
| 8 | Global Statutes bölümü (sağ) | Panel | Autonomy Level, Quorum Threshold, Safety Baseline |
| 9 | "View Constitution" butonu | Buton | (Stub) |
| 10 | New Amendment Modal | Modal | Statute title input, constitutional impact textarea, Discard Draft / Seal and Propose butonları |

### ✅ Test Senaryoları

#### TC-POL-001: Öneri Listesi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/policy-proposals` sayfasını aç | Tüzük versiyonu (v9.4.2-STABLE) ile header ve öneri kartları yüklenir |
| 2 | Öneri kartlarını kontrol et | Başlık, scope badge, tarih, status badge, quorum progress bar, imzacılar, git SHA mevcut |
| 3 | COMMITTED durumlu öneriyi kontrol et | Status badge mevcut |
| 4 | PROPOSED durumlu öneriyi kontrol et | Status badge mevcut |

#### TC-POL-002: Öneri Seçimi ve Detay
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir öneri kartına tıkla | Sağ panelde Amendment Detail yüklenir |
| 2 | Anayasal etki açıklamasını kontrol et | Metin dolu |
| 3 | Amendment ID ve yazarı kontrol et | Doğru bilgiler |

#### TC-POL-003: Sign-off Verme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | PROPOSED durumlu bir öneriyi seç | "Kurumsal Sign-off Ver" butonu aktif |
| 2 | Butona tıkla | `POST /api/v1/governance/proposals/{id}/approve` çağrılır (note/comment ile) |
| 3 | Quorum progress bar'ı kontrol et | İmzacı sayısı artmış olmalı |

#### TC-POL-004: Sign-off Buton Disabled
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | COMMITTED durumlu bir öneriyi seç | "Kurumsal Sign-off Ver" butonu disabled |

#### TC-POL-005: Yeni Amendment Oluşturma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "New Amendment" butonuna tıkla | Modal açılır |
| 2 | Statute title: "Veri Erişim İzleme Politikası" gir | Input dolar |
| 3 | Constitutional impact: "Tüm veri erişim talepleri denetim altına alınacak, 7/24 loglama zorunluluğu eklenecek" gir | Textarea dolar |
| 4 | "Seal and Propose" butonuna tıkla | Öneri oluşturulur, modal kapanır, listeye eklenir |
| 5 | "Discard Draft" tıkla (iptal) | Modal kapanır, öneri oluşturulmaz |

#### TC-POL-006: Global Statutes
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sağ sidebar'daki Global Statutes'u kontrol et | Autonomy Level: "TIER-4 REGULATED", Quorum Threshold: "MAJORITY 66%", Safety Baseline: "STRICT ISO-42001" |

---

## 21. Project Factory

### 📌 Sayfanın Amacı
Proje Fabrikası portfolyo görünümü. Global arşiv indeksi ve tüm Project Factory örneklerinin yönetimi. **1274 satırlık dev client bileşeni.** Politika otopilotu, yönetim kurulu kararları, PR planları, uçtan uca politika yaşam döngüsü.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Rebuild Archive Index" butonu | Buton | Arşiv indeksini yeniden oluşturur |
| 2 | 4 Metrik Kartı | Kart | Total Projects, Closed & Archived, Open Human Gates, Blocked Pipelines |
| 3 | Portfolio Intelligence sekmeleri | Tab | Risk Patterns, Templates, Agent performance, Learning Recommendations |
| 4 | Run Intelligence butonu | Buton | Portfolyo zeka analizi çalıştırır |
| 5 | Publish CEO Suggestions butonu | Buton | CEO önerilerini yayınlar |
| 6 | Policy Autopilot bölümü | Panel | Politika önerileri listesi |
| 7 | Run Policy Autopilot butonu | Buton | |
| 8 | Approve/Defer/Reject butonları (Autopilot) | Buton | Her politika önerisi için |
| 9 | Policy Board Decision bölümü | Panel | Kurul seviyesi onay |
| 10 | Board Approve/Revision/Reject butonları | Buton | |
| 11 | Apply Preview butonu | Buton | |
| 12 | PR Plan Prepare/Create butonu | Buton | Draft PR oluşturma |
| 13 | PR Review Run/Decision butonları | Buton | |
| 14 | Final Decision butonları | Buton | approve/reject/request revision |
| 15 | Arama/filtre/sıralama/pagination | Form | Proje arama ve filtreleme |

### ✅ Test Senaryoları

#### TC-PROJ-001: Portfolyo Metrikleri
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/project-factory` sayfasını aç | 4 metrik kartı yüklenir |
| 2 | Total Projects kartını kontrol et | Sayısal değer |
| 3 | Open Human Gates kartını kontrol et | Bekleyen insan onayı sayısı |
| 4 | Blocked Pipelines kartını kontrol et | Engellenen pipeline sayısı |

#### TC-PROJ-002: Arşiv İndeksini Yeniden Oluşturma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Rebuild Archive Index" butonuna tıkla | `POST /api/v1/project-factory/archive-index/rebuild` çağrılır |
| 2 | İşlem tamamlanır | İndeks güncellenir |

#### TC-PROJ-003: Policy Autopilot — Onay Döngüsü
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Run Policy Autopilot" tıkla | Otopilot çalışır, politika önerileri listelenir |
| 2 | Bir önerinin "Approve for Policy Board" butonuna tıkla | Öneri yönetim kuruluna iletilir |
| 3 | Board seviyesinde "Approve for Preview" tıkla | Apply preview oluşturulur |
| 4 | "Apply Preview" tıkla | Değişiklik önizlemesi gösterilir |

#### TC-PROJ-004: PR Plan ve Oluşturma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Prepare PR Plan" tıkla | `POST .../policy-pr-plan/{id}/prepare` çağrılır |
| 2 | Evidence pack'i kontrol et | Kanıt paketi yüklenir |
| 3 | "Create Draft PR" tıkla | `POST .../policy-pr-plan/{id}/create-pr` çağrılır |
| 4 | Oluşturma durumunu kontrol et | Status endpoint'i polling ile izlenir |

#### TC-PROJ-005: Arama ve Filtreleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Arama alanına "e-commerce" yaz | Sonuçlar filtrelenir |
| 2 | Status dropdown'dan "active" seç | Sadece aktif projeler |
| 3 | Risk level dropdown'dan "high" seç | Sadece yüksek riskli projeler |
| 4 | Sıralama değiştir | Sonuçlar yeniden sıralanır |
| 5 | Sonraki sayfaya geç (pagination) | Yeni sayfa yüklenir |

---

## 22. Prompt Studio

### 📌 Sayfanın Amacı
Ajan ruh/prompt düzenleyicisi. AI ajan "soul"larını (sistem prompt'ları / kişilik tanımları) düzenleme stüdyosu. Tüm ajanları listeler ve her birinin soul içeriği için tam ekran markdown editörü sağlar.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "YENI AJAN" butonu | Buton | Yeni ajan oluşturur (stub) |
| 2 | Arama input (sol sidebar) | Input | Ajan adı/açıklaması ile arama |
| 3 | Ajan listesi kartları (sol) | Kart listesi | İkon, ad, açıklama, seçili durum vurgusu, chevron |
| 4 | Editör header | Header | Ajan adı + "SOUL" etiketi, versiyon (v2.4.0), "Active Runtime" durum göstergesi |
| 5 | "Reset to Defaults" butonu | Buton | (Stub) |
| 6 | "DEPLOY SOUL" butonu | Buton | Değişiklikleri kaydeder (loading spinner) |
| 7 | Tam ekran monospace textarea | Textarea | Markdown soul içeriği düzenleme |
| 8 | Floating meta göstergeleri | Badge | "Markdown Format", "Token Efficient" |
| 9 | Boş durum (ajan seçilmemişse) | Panel | Beyin ikonu + seçim yapılması uyarısı |

### ✅ Test Senaryoları

#### TC-PROMPT-001: Ajan Listesi ve Seçim
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/prompt-studio` sayfasını aç | Sol sidebar'da ajan listesi, sağda boş editör durumu görünür |
| 2 | Ajan listesini kontrol et | Her kartta ikon, ad, açıklama mevcut |
| 3 | Skeleton loading durumunu kontrol et | Veri yüklenirken skeleton gösterilir |
| 4 | Bir ajan kartına tıkla | `GET /api/v1/harness/agents/{name}` çağrılır, soul içeriği editöre yüklenir |
| 5 | Seçili kartın vurgulamasını kontrol et | Diğer kartlardan farklı stil |

#### TC-PROMPT-002: Ajan Araması
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Arama alanına "security" yaz | Sadece adında/açıklamasında "security" geçen ajanlar |
| 2 | Arama alanını temizle | Tüm ajanlar geri döner |

#### TC-PROMPT-003: Soul Düzenleme ve Deploy
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir ajan seç | Soul içeriği textarea'ya yüklenir (monospace font) |
| 2 | İçeriği düzenle: sonuna "## Yeni Görev\nGüvenlik taraması yap" ekle | Textarea güncellenir |
| 3 | "DEPLOY SOUL" butonuna tıkla | Loading spinner gösterilir, `PUT /api/v1/harness/agents/{name}` çağrılır |
| 4 | Başarılı kayıt | Spinner durur, başarı bildirimi |

#### TC-PROMPT-004: Editör Metadata
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Editör header'ı kontrol et | Ajan adı + "SOUL" etiketi, versiyon (v2.4.0), "Active Runtime" göstergesi |
| 2 | Floating badge'leri kontrol et | "Markdown Format" ve "Token Efficient" |

#### TC-PROMPT-005: Boş Durum
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Hiçbir ajan seçmeden sağ paneli kontrol et | Beyin ikonu + "Bir ajan seçin" mesajı |

---

## 23. Proof Events

### 📌 Sayfanın Amacı
Değiştirilemez olay defteri — tüm yönetişim lineage kayıtlarını (karar denetim izi) gösterir. Her otonom kararın kurcalamaya karşı korumalı kaydı.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Breadcrumb (Home → Proof Fabric → Event Ledger) | Breadcrumb | |
| 2 | Ant Design Table | Tablo | Component, Decision Type, Outcome, Confidence Score, Integrity Hash (kopyalanabilir), Created At |
| 3 | Hash kopyala butonu | Buton | Panoya kopyalar |
| 4 | "Back to Proof Fabric" butonu | Buton | Geri navigasyon |
| 5 | "Open Snapshots" butonu | Buton | Snapshots sayfasına yönlendirir |
| 6 | Pagination (20/sayfa) | Pagination | |

### ✅ Test Senaryoları

#### TC-PROOF-E-001: Olay Defteri
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/proof/events` sayfasını aç | Breadcrumb ve tablo yüklenir |
| 2 | Tablo sütunlarını kontrol et | Component, Decision Type, Outcome, Confidence, Integrity Hash, Created At |
| 3 | En az 1 kayıt mevcut | Tablo boş olmamalı |

#### TC-PROOF-E-002: Hash Kopyalama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir satırdaki Integrity Hash yanındaki kopyala ikonuna tıkla | Hash panoya kopyalanır |
| 2 | Bir editöre yapıştır | Tam hash doğru yapıştırılır |

#### TC-PROOF-E-003: Navigasyon
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | "Open Snapshots" butonuna tıkla | `/proof/snapshots` sayfasına yönlendirilir |
| 2 | "Back to Proof Fabric" tıkla | Proof Fabric sayfasına geri dönülür |

---

## 24. Proof Snapshots

### 📌 Sayfanın Amacı
Yönetişim zincirinin mühürlenmiş Merkle ağaç anlık görüntüleri — değiştirilemezliğin kriptografik kanıtı. **Aktif platform oturumu gerektirir.**

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Breadcrumb | Breadcrumb | |
| 2 | Oturum kimlik doğrulama kontrolü | Alert | Oturum yoksa uyarı |
| 3 | Ant Design Table | Tablo | Snapshot Name, Seal Status (SEALED tag), Event Count, Merkle Root (kopyalanabilir), Snapshot Hash (kopyalanabilir), Created At, Action |
| 4 | Merkle Root kopyala | Buton | |
| 5 | Snapshot Hash kopyala | Buton | |
| 6 | "Inspect" linki | Link | Snapshot detayını görüntüler |
| 7 | Pagination (20/sayfa) | Pagination | |

### ✅ Test Senaryoları

#### TC-PROOF-S-001: Oturum Kontrolü
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Oturum açmadan `/proof/snapshots` aç | Uyarı alert gösterilir: "Aktif oturum gerekli" |
| 2 | Oturum açtıktan sonra aç | Tablo yüklenir |

#### TC-PROOF-S-002: Snapshot Tablosu
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Tablo sütunlarını kontrol et | Name, Seal Status, Event Count, Merkle Root, Snapshot Hash, Created At, Action |
| 2 | Seal Status tag'ini kontrol et | "SEALED" tag'i mevcut |

#### TC-PROOF-S-003: Hash Kopyalama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Merkle Root kopyala | Hash panoya kopyalanır |
| 2 | Snapshot Hash kopyala | Farklı hash panoya kopyalanır |

#### TC-PROOF-S-004: Inspect
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Bir snapshot'ın "Inspect" linkine tıkla | Snapshot detay sayfası/modal açılır |


---

## 25. Repair Lab

### 📌 Sayfanın Amacı
Otonom AGI UI Onarım Laboratuvarı (Phase 32). Yama turnuvaları (patch tournaments), doğrulayıcı matrisleri (verifier matrices), PR-Agent yönetişimi ve kanıt galerileri için test ve doğrulama merkezidir. Lab, FinOps ve Yönetişim (Governance) görünümlerini barındırır.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Execute Benchmark" butonu | Buton | Otonom onarım benchmark'ı tetikler |
| 2 | Lab / FinOps / Governance görünüm geçişleri | Toggle/Tab | Lab modu, maliyet odaklı mod ve yönetişim modları arası geçiş |
| 3 | PatchTournamentBoard bileşeni | Panel | Yama turnuva durumları |
| 4 | PRAgentGovernancePanel | Panel | PR inceleme, açıklama ve yama uygulama aksiyonları |
| 5 | Self-Repair Runs tablosu | Tablo | Risk seviyeleri, sandbox durumları ve etkilenen dosyalar |
| 6 | Taskflow Runs tablosu | Tablo | İş akışı adımları, gate durumları ve metrikler |

### ✅ Test Senaryoları

#### TC-REPAIR-001: Benchmark Çalıştırma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/repair-lab` sayfasını aç | Lab modu varsayılan olarak yüklenir |
| 2 | "Execute Benchmark" butonuna tıkla | `POST /api/v1/repair-lab/cases/{id}/trigger-autonomous-repair?target_url=...` veya ilgili benchmark tetiklenir |
| 3 | Durum izlemeyi doğrula | İlerleme adımları UIRepairTimeline'da görünür |

#### TC-REPAIR-002: PR Yönetişim Aksiyonları
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | PRAgentGovernancePanel'de bir yama seç | Yama detayları ve diff'leri yüklenir |
| 2 | "Apply Patch" butonuna tıkla | `POST /api/v1/repair-lab/cases/{id}/apply-patch` çağrılır |

---

## 26. Repair Memory

### 📌 Sayfanın Amacı
Otonom onarım belleği ve strateji öğrenme motoru. Farklı alt sistemlerin onarım başarı oranlarını ve hangi stratejilerin cezalandırılıp hangilerinin terfi (promoted) ettirildiğini gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Subsystem Success Heatmap kartları | Kart grid | Alt sistem adı, başarı/başarısızlık oranı ve progress bar |
| 2 | Strategy Trust & Efficiency tablosu | Tablo | Strateji adı, güven skoru (progress bar), başarı/rollback oranları ve durum tag'i |
| 3 | Penalized Negative Patterns listesi | Liste | Cezalandırılmış otonom stratejiler, ceza puanları ve etki alanı |

### ✅ Test Senaryoları

#### TC-REPMEM-001: Başarı Oranlarını İzleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/repair-memory` sayfasını aç | Isı haritası kartları ve strateji güven tablosu yüklenir |
| 2 | Strateji tablosunda sıralama yap | Güven skoruna göre sıralama doğru çalışmalı |

---

## 27. Safety

### 📌 Sayfanın Amacı
Sistem düzeyinde güvenlik korkuluk paneli. Güvenlik seviyelerini (NORMAL / SAFETY_FREEZE) kontrol eder, acil durum fallbacks (gpt-4o-mini geçişi, read-only izolasyon, git stable rollback) ve global dondurma (Emergency Freeze) aksiyonları barındırır. **API çağrısı içermez, durumlar simüle edilir.**

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | NORMAL / SAFETY_FREEZE toggle butonları | Butonlar | Sistem durumunu manuel değiştirir |
| 2 | "Execute Global Freeze" butonu | Buton | Acil durum kilidini tetikler (kırmızı ve belirgin) |
| 3 | Integrated Guardrails kartları | Kart grid | Health Index, Error Rate, Exposure limitleri progress bar ile |
| 4 | Safety Ledger timeline | Timeline | Güvenlik olayları log akışı |
| 5 | Fallback seçenekleri kartları | Kartlar | gpt-4o-mini, isolate tools, stable git rollback seçenekleri |

### ✅ Test Senaryoları

#### TC-SAFETY-001: Global Freeze Tetikleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/safety` sayfasını aç | Sistem "NORMAL" durumda yüklenir |
| 2 | "Execute Global Freeze" butonuna tıkla | Sistem "SAFETY_FREEZE" durumuna geçer, arayüzde kırmızı kilit ve uyarılar tetiklenir |
| 3 | "Reset" butonuna tıkla | Sistem tekrar "NORMAL" durumuna döner |

---

## 28. Self-Tuning

### 📌 Sayfanın Amacı
Otonom sistem parametre kalibrasyonu. Kalibrasyon önerilerini listeler, evolution feed akışını gösterir ve takılmış (stuck) durumları raporlar. **Her 30 saniyede bir otomatik yenilenir.**

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Calibration Matrix tablosu | Tablo | Parametre adı, mevcut/önerilen değer, güven %, etki ve aksiyonlar |
| 2 | "Uygula" (Approve) butonu | Buton | Öneriyi onaylar ve uygular |
| 3 | "Reddet" (Reject) butonu | Buton | Öneriyi reddeder |
| 4 | Evolution Feed | Liste | Evrim olay log akışı |
| 5 | Resilience Stress Panel | Panel | Dosya başına hata sayısı ve takılma durumları |

### ✅ Test Senaryoları

#### TC-TUNE-001: Öneri Kabul Etme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/self-tuning` sayfasını aç | Öneri kartları ve evrim akışı yüklenir |
| 2 | Bir kalibrasyon önerisinde "Uygula" butonuna tıkla | `POST /api/v1/repair-lab/tuning/suggestions/{id}/apply` (status: approved) çağrılır, kart durumu güncellenir |

---

## 29. System Health

### 📌 Sayfanın Amacı
Uptime izleme ve sistem telemetrisi. Diagnostikler, worker orkestrasyonu, 8 ana servis metriği, sistem yükü ve gecikme profillerini gösterir. Periyodik olarak 3sn, 5sn ve 10sn aralıklarla otomatik veriler yenilenir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Concurrency Ölçeklendirme butonları | Butonlar | Worker sayısını 1, 2, 4, 8 olarak ayarlar |
| 2 | Runtime Diagnostics "Repair" butonu | Buton | Otomatik onarılabilen hataları tetikler |
| 3 | 8 Servis Metriği grid | Grid | API, DB, Cache vb. durumları |
| 4 | Latency Profile bar chart | Grafik | 40 veri noktalı gecikme profili |

### ✅ Test Senaryoları

#### TC-HEALTH-001: Worker Ölçeklendirme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/system-health` sayfasını aç | Worker panelinde aktif slotlar görünür |
| 2 | Concurrency panelinde "4" butonuna tıkla | `POST /health/queue-scale` (concurrency: 4) çağrılır, worker'lar güncellenir |

---

## 30. Training

### 📌 Sayfanın Amacı
Kaos mühendisliği simülasyonları tatbikat paneli. İzole shadow cluster'larda çalıştırılan otonom sistem kurtarma drills geçmişini ve ayarlarını gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Initialize Drill" butonu | Buton | Manuel tatbikat başlatma modalını açar |
| 2 | Tatbikat listesi | Liste | Scenario, outcome (SUCCESS/POLICY_BREACH/etc.), duration |
| 3 | Auto-mode toggle | Switch | Otonom tatbikat modunu açar/kapatır |
| 4 | Simülasyon parametreleri | Panel | Chaos Density, Mean Recovery, Error Tolerance göstergeleri |

### ✅ Test Senaryoları

#### TC-TRAIN-001: Kaos Simülasyonu Başlatma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/training` sayfasını aç ve "Initialize Drill" butonuna tıkla | Senaryo seçim modalı açılır |
| 2 | Senaryoyu seç ve "Run" tıkla | `POST /governance/drills/trigger` çağrılır, tatbikat listesine "RUNNING" olarak eklenir |

---

## 31. UI Repair

### 📌 Sayfanın Amacı
**Projenin en kapsamlı sayfası (73KB, 1348 satır, 20+ sekme).** Phase 32 otonom UI onarımının komuta merkezidir. Tüm route sağlık matrisleri, soak doğrulama, proof paketleri, pilot yayılım ve GA operasyonları buradan yönetilir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Trigger Smoke Run" butonu | Buton | Arayüz smoke testlerini tetikler |
| 2 | 20+ Navigasyon Sekmesi | Tab Bar | Sekmeler arası geçiş |
| 3 | Continuous Monitoring toggle | Switch | Otomatik izleme ve onarımı açar/kapatır |
| 4 | Risk Threshold dropdown | Select | LOW/MEDIUM/HIGH/CRITICAL risk eşikleri |
| 5 | Repair Case Detay Modalı | Modal | Diagnostic, PR Review, Evidence, Timeline sekmeli yama modalı |
| 6 | "Apply Patch" butonu | Buton | Yama modalı içinden operator onayı ile yama uygular |

### ✅ Test Senaryoları

#### TC-UIREP-001: Sekme Geçişleri ve İzleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/ui-repair` sayfasını aç | 20+ sekme render edilir, ilk sekme aktiftir |
| 2 | Sekmeler arasında geçiş yap | Her sekmenin kendi alt paneli hatasız yüklenir |
| 3 | Bir hata vakasına tıklayıp modalı aç | Yama diff, ekran kanıtları ve console logları yüklenir |

---

## 32. Verifiers

### 📌 Sayfanın Amacı
Doğrulayıcı mesh (Verifier Mesh) panosu. Çok katmanlı kalite güvence altyapısının hassasiyet, latency ve hata durumlarını izler.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Arama input | Input | Doğrulayıcı adına göre filtreleme |
| 2 | "Optimize Mesh" butonu | Buton | (Stub) |
| 3 | Verifier kartları | Kart grid | Hassasiyet %, Latency, CRITV_FLAGS hataları |

### ✅ Test Senaryoları

#### TC-VERIF-001: Doğrulayıcı Filtreleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/verifiers` sayfasını aç | Doğrulayıcı kartları yüklenir |
| 2 | Arama kutusuna "syntax" yaz | Sadece adında syntax geçen doğrulayıcılar filtrelenir |

---

## 33. Workflows

### 📌 Sayfanın Amacı
İş akışları yaşam döngüsü yönetim arayüzü. Sistemdeki otonom orkestrasyonların ilerlemelerini, adım sayılarını ve durumlarını gösterir. **Her 10 saniyede bir otomatik yenilenir.**

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Create" butonu | Buton | Yeni iş akışı oluşturma formuna yönlendirir |
| 2 | Workflow kartları | Kart listesi | Durum ikonları (running animasyonu, completed, failed), step progress bar'ı |
| 3 | Kart inspect aksiyonu | Link | `/workflows/${id}` detayına yönlendirir |

### ✅ Test Senaryoları

#### TC-WF-001: İş Akışı İnceleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/workflows` sayfasını aç | Aktif iş akışları listelenir |
| 2 | Bir kartın üzerine gelip "Inspect" butonuna tıkla | `/workflows/${id}` detay sayfasına yönlendirilir |


---

## 34. Ops: Handover Status (Rollout Center)

### 📌 Sayfanın Amacı
Pilot dağıtımlarını, canlı dağıtım düğümlerini ve teslimat bütünlüğünü (handover integrity) takip eden **Rollout Center** ekranıdır. Otonom görevlerin askıya alınmasını sağlayan acil durum müdahale mekanizmaları içerir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Rollout Kartları (`EliteRolloutCard`) | Kart grid | Durum tag'leri, PID, lansman zamanı, progress bar |
| 2 | "Verify Audit Bundle" butonu | Buton | AuditBundleModal açar |
| 3 | "Emergency Freeze" butonu | Buton | Rollout'u dondurur (kilit overlay'i ekler) |
| 4 | "Live Decision Logs" butonu | Buton | `/workflows/${id}` adresine yönlendirir |

### ✅ Test Senaryoları

#### TC-OPS-HS-001: Rollout Freeze ve Acil Kilit
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/ops/handover-status` sayfasını aç | Pilot rollout kartları listelenir |
| 2 | Bir kartın "Emergency Freeze" butonuna tıkla | Onay dialogu açılır |
| 3 | Onay kutusunda "Evet" tıkla | Kart donmuş duruma geçer, kırmızı lock overlay'i kaplanır |

---

## 35. Ops: Launch Gates

### 📌 Sayfanın Amacı
AGI üretim hazırlık kontrol noktası (**Launch Gates**). Bütçe, yönetişim, quorum ve doğruluk alanındaki 4 koruyucu kapıyı izler ve handovere izin verir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Circular Mission Readiness Gauge | Gösterge | Dinamik hazırlık yüzdesi |
| 2 | Gate Cards | Kart grid | BUDGET-GUARD, GOVERNANCE-GUARD, QUORUM-GATE, ACCURACY-GATE durumları |
| 3 | "Handover Tetikle" (Trigger Handover) butonu | Buton | Sadece tüm gate'ler PASS ise aktifleşir |

### ✅ Test Senaryoları

#### TC-OPS-LG-001: Handover Tetikleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/ops/launch-gates` sayfasını aç | Hazırlık yüzdesi ve gate durumları yüklenir |
| 2 | Tüm gate'ler PASS olduğunda "Handover Tetikle" butonuna tıkla | Handover tetiklenir, onay mesajı gösterilir |

---

## 36. Compliance: Audit Bundles

### 📌 Sayfanın Amacı
Otonom teslimatların ve dry-run'ların denetim kayıtlarını içeren mühürlü ZIP paketleri arşivi.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Arama input kutusu | Input | Paket adına göre filtreleme |
| 2 | Bundles tablosu | Tablo | ZIP adı, purpose, status tag'i (sealed), seal SHA256 ve indirme butonu |
| 3 | "Download" butonu | Buton | ZIP arşivini indirmeyi simüle eder |

### ✅ Test Senaryoları

#### TC-COMP-AB-001: Paket Arama ve İndirme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/compliance/audit-bundles` sayfasını aç | Mühürlü paketlerin listesi yüklenir |
| 2 | Arama kutusuna "LAUNCH" yaz | Sadece LAUNCH içeren paketler gösterilir |
| 3 | Bir paketin yanındaki "Download" butonuna tıkla | İndirme işlemi tetiklenir |

---

## 37. Governance: Lineage

### 📌 Sayfanın Amacı
Otonom kararların (onarımlar, politikalar) geçmişini ve nedensellik bağlarını gösteren karar soyağacı izleyicisidir. Telemetry payload JSON verilerini katlanabilir terminal ile gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Lineage Satır Kartları | Kart listesi | Rasyonel, güven skoru, durum badge'i, verifikasyon seal hash'i |
| 2 | Terminal Toggle butonu | Buton | JSON telemetry terminalini açar/kapatır |
| 3 | "Inspect Evidence" butonu | Buton | İlgili kanıta yönlendirir |
| 4 | "View Root Cause" butonu | Buton | En baştaki ata karara (root cause) trace eder |

### ✅ Test Senaryoları

#### TC-GOV-LIN-001: Telemetry JSON İnceleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governance/lineage` sayfasını aç | Lineage satırları kronolojik sırada listelenir |
| 2 | Bir satırın sonundaki terminal toggle butonuna tıkla | Altında raw telemetry JSON bloğu açılır |

---

## 38. Governor: Observability Dashboard

### 📌 Sayfanın Amacı
Güvenlik alarmları, drift metrikleri ve karar doğruluğu oranlarını izleyen yönetişim sağlık kokpitidir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Refresh" butonu | Buton | Alarmları, driftleri ve metrikleri yeniler |
| 2 | "Trigger Scan" butonu | Buton | Manuel güvenlik taraması başlatır |
| 3 | KPI Strip kartları | Kartlar | Open Alerts, Active Drifts, Avg Accuracy, System Health |
| 4 | Recent Alerts (AlertTable) | Tablo | Onay (Acknowledge) ve Inspect butonları |

### ✅ Test Senaryoları

#### TC-GOV-OBS-001: Manuel Tarama Tetikleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/observability` sayfasını aç | Güncel alarm ve metrik özetleri yüklenir |
| 2 | "Trigger Scan" butonuna tıkla | Tarama tetiklenir, ardından metrikler otomatik yenilenir |

---

## 39. Governor: Scorecard

### 📌 Sayfanın Amacı
Karar kalitesi, latency performansı, SLO uyumluluk durumu ve fatura risklerini gösteren karne ekranı.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Toplam Karar / Karar Doğruluğu kartları | Kartlar | % oran ve progress bar |
| 2 | Son Karar Çıktıları tablosu | Tablo | SUCCESS/FAILED/REGRESSION tag'leri ve kalite tag'leri |
| 3 | Resilience SLO Monitoring | Panel | SLO hedefleri ve durumları listesi |

### ✅ Test Senaryoları

#### TC-GOV-SC-001: SLO Durum Kontrolü
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/scorecard` sayfasını aç | SLO hedefleri ve ortalama latency değerleri yüklenir |
| 2 | Resilience SLO tablosunu kontrol et | Sınır değerleri ve durum göstergeleri dolu olmalı |

---

## 40. Governor: Proof Fabric

### 📌 Sayfanın Amacı
Değişmezlik katmanı izleyicisi. Cryptographic Merkle anlık görüntülerini ve denetçi ağ durumlarını listeler.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Son Kanıt Olayları tablosu | Tablo | Event type tag, integrity hash |
| 2 | Kriptografik Snapshotlar listesi | Liste | Verify ve Export tooltips |
| 3 | "Yeni Snapshot Mühürle" butonu | Buton | Yeni mühürleme başlatır |
| 4 | Verifier Network Status | Kolonlar | Internal, Prime, External denetçi durumları |

### ✅ Test Senaryoları

#### TC-GOV-PF-001: Yeni Snapshot Mühürleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/proof` sayfasını aç | Snapshot listesi yüklenir |
| 2 | "Yeni Snapshot Mühürle" butonuna tıkla | Simüle edilmiş mühürleme süreci başlar, listeye yeni mühürlü satır eklenir |

---

## 41. Governor: Alerts Center

### 📌 Sayfanın Amacı
Yönetişim alarmlarını filtreleme ve onaylama (acknowledge) merkezi.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Status Filter dropdown | Select | Open, Acknowledged, Resolved, Suppressed filtreleri |
| 2 | AlertTable | Tablo | Alert satırları ve "Action Required" etiketleri |
| 3 | "Acknowledge" butonu | Buton | Alarmı onaylar |

### ✅ Test Senaryoları

#### TC-GOV-AL-001: Alarm Onaylama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/alerts` sayfasını aç | Açık alarmlar listelenir |
| 2 | Bir alarmın yanındaki "Acknowledge" butonuna tıkla | Ack mutation tetiklenir, alarm "Acknowledged" durumuna geçer |

---

## 42. Governor: Behavioral Drift Monitor

### 📌 Sayfanın Amacı
Yönetişim davranışlarındaki ve karar kalıplarındaki uzun vadeli sapmaları (drift) izler.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | System Analysis Banner | Alert | 24 saatlik verinin 14 günlük baseline ile karşılaştırılma bilgisi |
| 2 | Drift Table | Tablo | Sapma metrikleri listesi |

### ✅ Test Senaryoları

#### TC-GOV-DR-001: Sapma İzleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/drifts` sayfasını aç | Aktif sapma durumları ve skorları tablosu görüntülenir |

---

## 43. Governor: Chaos Engineering Lab (Resilience Drills)

### 📌 Sayfanın Amacı
Yönetişim direncini test etmek için kontrollü kaos senaryolarını tetikleme laboratuvarı.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Start New Drill" butonu | Buton | Kaos senaryo seçim modalını açar |
| 2 | Scenario Type & Target Domain | Modal Form | Senaryo tipi ve hedef alan seçimi |
| 3 | Drill History tablosu | Tablo | Scenario type, target, status tag, duration |

### ✅ Test Senaryoları

#### TC-GOV-DRL-001: Kaos Drilli Başlatma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/drills` sayfasını aç ve "Start New Drill" butonuna tıkla | Kaos modalı açılır |
| 2 | Scenario: "CONFLICT_STORM", Domain: "WORKFLOW" seç ve "Run" tıkla | `POST /governance/governor/resilience/drills` tetiklenir, drill "RUNNING" olarak başlar |

---

## 44. Governor: Aktif Eskalasyonlar

### 📌 Sayfanın Amacı
İnsan operatörlere (PRIME) veya quorum seviyelerine iletilmiş aktif eskalasyon durumları ve manual override kontrolleri.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | SLA / Yaş badge'leri | Badge | SLA süresi renklendirilmiş durumları (<1s yeşil, >24s kırmızı) |
| 2 | "İşlem Yap" aksiyon menüsü | Dropdown | Kabul Et (Ack), Çöz (Resolve), İptal (Cancel) |

### ✅ Test Senaryoları

#### TC-GOV-ESC-001: Eskalasyon Manuel Çözümü
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/escalations` sayfasını aç | Bekleyen eskalasyonlar SLA bilgileriyle yüklenir |
| 2 | Bir satırda "İşlem Yap" -> "Çöz (Resolve)" seçeneğine tıkla | Gerekçe formu açılır, onaylandıktan sonra durum "Resolved" olur |

---

## 45. Governor: Federated Governance View

### 📌 Sayfanın Amacı
Çoklu bağımsız alan yöneticileri (domain governors) tarafından alınan ortak meta-kararların dökümüdür.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Active Domains Count | Kart | Aktif federasyon bölge sayısı |
| 2 | Son Meta Kararlar tablosu | Tablo | Winning Domain tag, risk class, applied constraints, timestamp |

### ✅ Test Senaryoları

#### TC-GOV-FED-001: Meta Kararları İnceleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/federated` sayfasını aç | Son meta-kararlar ve uygulanan kısıtlar listelenir |

---

## 46. Governor: Outcomes

### 📌 Sayfanın Amacı
Geçmiş kararları ve bunların kalite sınıflarını (OPTIMAL, SUBOPTIMAL, REGRESSION vb.) listeleyen analiz ekranı.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Outcomes Table | Tablo | Decision, Final Outcome, Quality (tag), Latency, Timestamp |

### ✅ Test Senaryoları

#### TC-GOV-OUT-001: Karar Sınıflarını Filtreleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/outcomes` sayfasını aç | Karar dökümleri ve optimallik dereceleri listelenir |

---

## 47. Governor: Operational Resilience

### 📌 Sayfanın Amacı
Devre kesicilerin (circuit breakers) ve alt yönetişim alanlarının anlık çalışma modlarını (Advisory / Enforcing) izler.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Degraded Alert | Alert | Eğer bütünlük %100 altındaysa acil durum modu uyarısı |
| 2 | Governor Domain Runtime Status tablosu | Tablo | Domain name, status (Healthy/Degraded/etc. tag'li), Failure count |

### ✅ Test Senaryoları

#### TC-GOV-RES-001: Devre Kesici Kontrolü
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/resilience` sayfasını aç | Her bir domain'in durumu, hata sayısı ve advisory/enforcing çalışma modu listelenir |

---

## 48. Learning: Adaptation Candidates

### 📌 Sayfanın Amacı
AI öğrenme sistemi tarafından üretilen otonom davranış adaptasyonu önerilerini listeler ve uygular.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Adaptation Table | Tablo | Strategy (Rocket icon), Confidence Progress Bar, Action |
| 2 | "Apply" butonu | Buton | Aday adaptasyon stratejisini onaylar ve uygular |

### ✅ Test Senaryoları

#### TC-LRN-AC-001: Aday Adaptasyon Uygulama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/learning/adaptation-candidates` sayfasını aç | Adaylar listelenir |
| 2 | Bir aday satırında "Apply" butonuna tıkla | `/api/v1/learning/adaptation-candidates/${id}/apply` POST tetiklenir, onay toast'u gelir |

---

## 49. Learning: Error Fingerprints Ledger

### 📌 Sayfanın Amacı
Hata parmak izleri kayıt defteri. Tekrarlayan hata kalıplarını ve bunların frekanslarını gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Recurrence Progress Bar | Progress | Hataların tekrarlanma sıklığı göstergesi |
| 2 | "Analyze" butonu | Buton | `/learning/fingerprints/${id}` detay analizine yönlendirir |
| 3 | Copy ID butonu | Buton | Parmak izi UUID hash'ini panoya kopyalar |

### ✅ Test Senaryoları

#### TC-LRN-FP-001: Hata Parmak İzi Analizi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/learning/fingerprints` sayfasını aç | Tekrarlayan hata kalıpları listelenir |
| 2 | Bir satırın sonundaki "Analyze" butonuna tıkla | İlgili hata analiz detay sayfasına yönlendirir |

---

## 50. Learning: Negative Patterns Blacklist

### 📌 Sayfanın Amacı
Cezalandırılmış otonom stratejilerin ve anti-pattern kara listesinin yönetimi.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Skull Watermark Table | Tablo | Arka planda kuru kafa fligranlı ceza tablosu |
| 2 | Penalty Weight Tag | Tag | Ceza ağırlık yüzdesi (örn. %80 PENALTY, kırmızı tag) |

### ✅ Test Senaryoları

#### TC-LRN-NP-001: Kara Liste İnceleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/learning/negative-patterns` sayfasını aç | Cezalandırılmış otonom davranışlar ve ceza oranları listelenir |

---

## 51. Learning: Strategy Memory

### 📌 Sayfanın Amacı
Daha önce uygulanmış otonom adaptasyon stratejilerinin performans geçmişini ve güven indekslerini tutar.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Trust Score Progress bar | Progress | Güven endeksi yüzdesi ve mor çubuk |
| 2 | Latency Zap ikonu | İkon | Gecikme milisaniye değeri |

### ✅ Test Senaryoları

#### TC-LRN-SM-001: Güven Skoru Sıralaması
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/learning/strategy-memory` sayfasını aç | Stratejiler güven skorlarına göre azalan sırada listelenir |

---

## 52. Fleet: Agent Registry

### 📌 Sayfanın Amacı
Filodaki tüm kayıtlı ajanların ad, rol, trust skoru ve güncel yük değerleriyle izlendiği ana sicil defteridir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Arama kutusu & "Yenile" butonu | Form | Ajan arama ve listeyi refetch etme |
| 2 | Durum Tag'leri | Tag | IDLE(yeşil), ASSIGNED(mavi), PAUSED(cyan), QUARANTINED(kırmızı) |
| 3 | "Karantinaya Al" butonu | Buton | Ajanı karantinaya alır (SafetyOutlined ikonu) |
| 4 | "Detaylar" butonu | Buton | Ajan detay kartını açar |

### ✅ Test Senaryoları

#### TC-FLT-AG-001: Ajan Karantinaya Alma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/fleet/agents` sayfasını aç | Ajan listesi yüklenir |
| 2 | "IDLE" durumlu bir ajanın yanındaki "Karantinaya Al" butonuna tıkla | Ajan karantinaya alınır, tag'i kırmızı "QUARANTINED" olur ve buton devre dışı kalır |

---

## 53. Fleet: Operations Controls

### 📌 Sayfanın Amacı
Ajan filosu için sistem genelinde rebalance (yük dengeleme) ve acil durum duraklatma kontrollerini tetikler.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Rebalance" butonu | Buton | Filo yükünü kuyruklar arası yeniden dengeler |
| 2 | Acil durum butonları (Tümünü durdur vb.) | Butonlar | Arka plan kısıtları nedeniyle şu an tooltip açıklamalarıyla kilitlidir |

### ✅ Test Senaryoları

#### TC-FLT-OP-001: Yük Dengeleme Tetikleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/fleet/operations` sayfasını aç | Kontrol kartları yüklenir |
| 2 | "Rebalance" butonuna tıkla | `/fleet/ops/rebalance` POST isteği gider ve rebalance işlemi onay bildirimi alınır |

---

## 54. Federation: Domain Conflict Management

### 📌 Sayfanın Amacı
Farklı yönetici alanlar arasındaki karar uyumsuzluklarını ve durum çakışmalarını listeler ve çözümlenmesini sağlar.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Alan A ve Alan B kararları | Hücreler | Karşılaştırmalı alan kararları ve `SwapOutlined` ikonu |
| 2 | "Çözüldü İşaretle" butonu | Buton | Çakışmayı manuel çözüldü olarak işaretler |

### ✅ Test Senaryoları

#### TC-FED-CF-001: Çakışma Çözümleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/federation/conflicts` sayfasını aç | Açık çakışmalar tablosu yüklenir |
| 2 | Bir çakışma satırındaki "Çözüldü İşaretle" butonuna tıkla | PATCH request gönderilir, çakışma listeden kaldırılır |


---

## 55. Approvals Detail Page

### 📌 Sayfanın Amacı
Otonom kararların onay beklediği geçit detay arayüzü (`/approvals/[id]`). İnsan operatörün gerekçe belirterek onay veya red vermesini sağlar.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Durum Tag'leri | Tag | PENDING, APPROVED, REJECTED durum göstergeleri |
| 2 | Technical Context JSON bloğu | Code | Monospace teknik veri bloğu |
| 3 | Operator Intervention Alanı | Textarea | Operatör karar notu (boş bırakılamaz) |
| 4 | "APPROVE & SEAL" butonu | Buton | Kararı mühürler ve onaylar |
| 5 | "REJECT" butonu | Buton | Kararı reddeder |

### ✅ Test Senaryoları

#### TC-DET-APP-001: Yama Kararı Mühürleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/approvals/{id}` sayfasını aç | Detay verileri ve "PENDING" durumu yüklenir |
| 2 | Karar Notu alanına "Yama test edildi, üretime hazır" yaz | Alan dolar |
| 3 | "APPROVE & SEAL" butonuna tıkla | `/api/v1/governance/approvals/{id}/decide` POST mutation tetiklenir, sayfa APPROVED olarak güncellenir |

---

## 56. Axiology Detail Page

### 📌 Sayfanın Amacı
Aksiyolojik (etik/değer uyum) değerlendirme analizi detay sayfası (`/axiology/[id]`). Kararların provenance mühürlerini ve düzeltici eylem önerilerini gösterir.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Decision Tag'leri | Tag | approve(tik), flag(uyarı), reject(hata) ikonlu tagler |
| 2 | Güvenlik Skorları progress bar'lar | Progress | Safety, Resource Integrity, Operational Risk çubukları |
| 3 | Target Content Code preview | Code | "PROVENANCE VERIFIED" mühürlü kod bloğu |

### ✅ Test Senaryoları

#### TC-DET-AXI-001: Detay İnceleme ve Skorlar
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/axiology/{id}` sayfasını aç | Etik uyum analizi, skor çubukları ve gerekçeler yüklenir |

---

## 57. Governor Alerts Detail Page

### 📌 Sayfanın Amacı
Otonom alarm kayıtlarının detaylı telemetri ve metrik ihlali verilerini gösterir (`/governor/alerts/[id]`).

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Severity-colored Card Border | Sınır | CRITICAL: kırmızı, HIGH: turuncu, WARNING: sarı çerçeve |
| 2 | AlertActionPanel butonları | Butonlar | Ack, Resolve, Suppress butonları |
| 3 | Evidence Payload JSON | Code | Monospace kanıt JSON verisi |

### ✅ Test Senaryoları

#### TC-DET-AL-001: Alarmı Çözme (Resolve)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/alerts/{id}` sayfasını aç | Alarm detayı ve severity çerçevesi yüklenir |
| 2 | `AlertActionPanel` üzerinde "Resolve" butonuna tıkla | `resolveAlert` mutation tetiklenir, durum "Resolved" olarak güncellenir |

---

## 58. Governor Drifts Detail Page

### 📌 Sayfanın Amacı
Konfigürasyon veya ajan davranış sapmalarının baseline karşılaştırma detaylarını gösterir (`/governor/drifts/[id]`).

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Circular Progress Score | Gösterge | Sapma oranı (score > 30% ise kırmızı, değilse mavi) |
| 2 | Evidence Payload | Code | Monospace sapma kanıt JSON bloğu |

### ✅ Test Senaryoları

#### TC-DET-DR-001: Sapma Oranı Raporu
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/drifts/{id}` sayfasını aç | Sapma skoru, karşılaştırma günleri ve raw JSON kanıtı yüklenir |

---

## 59. Governor Proof Snapshot Detail Page

### 📌 Sayfanın Amacı
Kriptografik olarak mühürlenmiş anlık görüntünün Merkle köklerini, imzalarını ve olay kapsamını listeler (`/governor/proof/snapshots/[id]`).

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | "Export Audit Bundle" butonu | Buton | Zip denetim paketini dışa aktarır |
| 2 | "Verify Integrity" butonu | Buton | Mühür doğruluğunu doğrular |
| 3 | Merkle Root & Snapshot Signature | Text | Monospace copyable hash stringleri |

### ✅ Test Senaryoları

#### TC-DET-PF-001: Mühür Bütünlüğü Doğrulama
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/proof/snapshots/{id}` sayfasını aç | Merkle kökü, seal durumu ve imza verileri yüklenir |
| 2 | "Verify Integrity" butonuna tıkla | Doğrulama simüle edilir ve bütünlük "OK" sonucu döner |

---

## 60. Governor Case Override & Escalation Detail

### 📌 Sayfanın Amacı
Bloklanmış veya askıya alınmış vakaların manuel aşılmasını (override) yönetir (`/governor/[id]`). Kritik/yüksek riskli vakalar için zorunlu gerekçe girilmesini şart koşar.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Hard Guardrail Alert | Alert | Risk seviyesi yüksekse "Hard Guardrail Active" kırmızı uyarısı |
| 2 | Gerekçe Textarea | Textarea | Manuel aşım gerekçesi (min 20 karakter) |
| 3 | Override Aksiyon butonları | Popconfirm | Force Approve, Replay, Archive, Cancel butonları |

### ✅ Test Senaryoları

#### TC-DET-GV-001: Zorunlu Gerekçeli Force Approve
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/governor/{id}` sayfasını aç | Vaka risk durumu ve askıya alınma nedenleri yüklenir |
| 2 | Gerekçe alanına 10 karakter yaz | Aksiyon butonları kilitli kalmalı |
| 3 | Gerekçeyi 20 karaktere tamamla: "Yedek veritabanı aktif edildi, işlem güvenli." | Aksiyon butonları aktifleşir |
| 4 | "Force Approve" butonuna tıkla | `POST /governance/governor/cases/{id}/override` tetiklenir, onay mesajı gösterilir |

---

## 61. Incident Detail & Mitigation Client

### 📌 Sayfanın Amacı
Oluşan arayüz veya sistem anomalilerinin loglarını gösteren ve mitige edilmesini sağlayan olay detay ekranıdır (`/incidents/[id]`).

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Manuel Çözüm Textarea & "ÇÖZ VE KAPAT" butonu | Form | Operatörün çözüm notu girmesi ve olayı kapatması |
| 2 | Raw Telemetry JSON | Code | Monospace anomali log ve telemetry verisi |
| 3 | Olay Yaşam Döngüsü timeline | Timeline | Keşif, inceleme ve çözüm adımları zamanı |

### ✅ Test Senaryoları

#### TC-DET-INC-001: Olayı Kapatma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/incidents/{id}` sayfasını aç | Kırmızı çerçeveli olay bilgileri ve telemetry yüklenir |
| 2 | Çözüm Notu alanına "Sistem yapılandırma dosyası düzeltildi." yaz | Alan dolar |
| 3 | "ÇÖZ VE KAPAT" butonuna tıkla | `/governance/incidents/{id}/resolve` çağrılır, olay kapalı durumuna geçer |

---

## 62. Learning Fingerprint Recurrence Detail

### 📌 Sayfanın Amacı
Hata parmak izinin tarihsel tekrarlanma dökümünü ve bunlara uygulanan otonom fix stratejilerini listeler (`/learning/fingerprints/[id]`).

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Sinyal Gücü Progress bar | Progress | Hatanın tekrarlanma gücü yüzdesi |
| 2 | Çözüm Geçmişi Tablosu | Tablo | Daha önce uygulanan stratejiler ve validasyon skorları |
| 3 | "Politika Teklifi Oluştur" butonu | Buton | Tekrarlanma > 10 ise aktifleşen otonom politika oluşturma |

### ✅ Test Senaryoları

#### TC-DET-LRN-001: Politika Teklifi Oluşturma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/learning/fingerprints/{id}` sayfasını aç | Hata dökümü ve strateji geçmişi yüklenir |
| 2 | Tekrarlanma sayısı 10 üzerindeyse "Politika Teklifi Oluştur" butonuna tıkla | Politika oluşturma süreci tetiklenir |

---

## 63. Project Factory Client Rollout Board

### 📌 Sayfanın Amacı
Bir yazılım projesinin kapsam alma, sandbox testleri, kod doğrulama raporları, aday paket oluşturma ve üretim canlısına geçiş aşamalarını yöneten **Project Factory** detay arayüzüdür (`/project-factory/[project_id]`).

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Operator Decision Action Panel | Tablar | WAITING FOR OPERATOR aşaması için Kapsamı Onayla / Revizyon Gerekli / Reddet sekmeleri |
| 2 | Sandbox Runner controls | Panel | Çalıştırıcı şablon seçimi, tetikleme, iptal butonları |
| 3 | Verification & Files outcome report | Tablo | Sandbox çalışma sonuçları, console çıktısı, değişen dosyalar |
| 4 | Candidate Review & Human Gate Console | Tablar | Risk değerlendirmesi, kalite skor kartı, operatör onay/red butonları |

### ✅ Test Senaryoları

#### TC-DET-PFAC-001: Sandbox Runner Çalıştırma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/project-factory/{project_id}` sayfasını aç | Aşamalar paneli yüklenir |
| 2 | Aşamayı "RUNNING" konumuna getirmek için Runner tetikle | Sandbox çalışır, console logları anlık olarak akar |
| 3 | Değişen dosyaları ve test verifikasyon raporunu kontrol et | Başarı yüzdesi gösterilmeli |

---

## 64. Workflow Detail Progress Trace

### 📌 Sayfanın Amacı
Aktif veya tamamlanmış iş akışı adımlarının durumlarını, loglarını, payload'larını ve ilgili yönetişim kapılarını gösteren detay ekranı (`/workflows/[id]`).

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Execution Plan adımları | Liste | Durum tag'leri (completed, running, failed, waiting) |
| 2 | Final Report structure viewer | Panel | İş akışı özeti, bulgular, riskler ve sonraki adımlar JSON formatında |
| 3 | Action Required / Reassign Panel | Panel | Bekleyen onaylar veya başarısız işler için reassign aksiyonları |

### ✅ Test Senaryoları

#### TC-DET-WF-001: İş Akışı Adımları Takibi
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/workflows/{id}` sayfasını aç | İş akışının durum adımları ve logları yüklenir |
| 2 | "Final Report" yapısını kontrol et | Bulgular ve sonraki adımlar ağaç yapısında listelenmeli |

---

## 65. Workflow Create Form

### 📌 Sayfanın Amacı
Otonom iş akışı oluşturma formu (`/workflows/create`). Şablonlar, öncelik düzeyleri ve kalite profillerinin seçilmesini sağlar.

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Title & Description input | Form | Akış başlığı ve açıklama (min satır 6) |
| 2 | Template dropdown | Select | default, research, coding, analysis şablonları |
| 3 | Priority Level dropdown | Select | LOW, MEDIUM, HIGH, CRITICAL seviyeleri |
| 4 | Quality Profile dropdown | Select | standard, high_precision, fast_track |
| 5 | "KAYDET" butonu | Buton | Yeni iş akışını kaydeder (RocketOutlined ikonu) |

### ✅ Test Senaryoları

#### TC-WF-CRT-001: Yeni İş Akışı Oluşturma
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/workflows/create` sayfasını aç | Form alanları yüklenir |
| 2 | Başlık: "Kod Güvenlik Denetimi", Şablon: "research", Öncelik: "HIGH" seç | Form alanları doldurulur |
| 3 | "KAYDET" butonuna tıkla | Akış kaydedilir, `/workflows` listesine yönlendirilir ve yeni akış eklenir |

---

## 66. Self-Tuning Scoped Calibration Table

### 📌 Sayfanın Amacı
Küresel anayasal limitlerin içinde kalmak kaydıyla departman/bölge bazlı konfigürasyon override dosyalarını ve YAML formatlı politikaları gösterir (`/self-tuning/scoped`).

### 🖱️ Etkileşim Noktaları

| # | Element | Tür | Açıklama |
|---|---------|-----|----------|
| 1 | Overlay Katmanları tablosu | Tablo | Departman kapsamı, override sayısı, durum tag'i (Active/Draft) |
| 2 | YAML Override Blokları | Panel | YAML string formatlı özelleştirilmiş politikalardan oluşan pre-formatted görünüm |
| 3 | "Düzenle" butonu | Buton | Özelleştirilmiş politikayı düzenlemeyi açar (visual) |

### ✅ Test Senaryoları

#### TC-TUNE-SCP-001: YAML Overrides İnceleme
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `/self-tuning/scoped` sayfasını aç | Departman katmanları tablosu ve YAML kod blokları yüklenir |



## 67. Cross-Page Testleri

### TC-CROSS-001: Oturum Yönetimi (Auth Flow)
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Giriş yapmadan `/fleet` adresine git | `/login` sayfasına yönlendirilmeli |
| 2 | Token'ı localStorage/cookie'den sil | Sonraki API çağrısında `/login?expired=true` yönlendirmesi |
| 3 | Geçerli giriş yap | Son bakılan sayfaya geri dönmeli |

### TC-CROSS-002: Sayfa Yüklenme Performansı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Her sayfanın ilk yüklenme süresini ölç | 3sn altında olmalı (bilgeapi-ops ve ui-repair hariç 5sn) |
| 2 | Console'da JavaScript hatası kontrol et | Kritik hata olmamalı |

### TC-CROSS-003: Sidebar Navigasyon Tutarlılığı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Sidebar'dan her sayfaya sırayla git | Tüm linkler çalışmalı, 404 olmamalı |
| 2 | Aktif sayfa vurgulamasını kontrol et | Her sayfada sidebar'daki ilgili link vurgulu |

### TC-CROSS-004: Otomatik Yenileme Kontrolü
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Dashboard: 5sn polling doğrula | `/health/dashboard` periyodik |
| 2 | Mesh: 5sn polling doğrula | `/mesh/status` periyodik |
| 3 | System Health: 3sn/5sn/10sn polling doğrula | Queue: 3sn, Dashboard: 5sn, Diagnostics: 10sn |
| 4 | Evolution: 30sn polling doğrula | `/evolution/state` periyodik |
| 5 | Self-Tuning: 30sn polling doğrula | Tuning suggestions periyodik |
| 6 | Workflows: 10sn polling doğrula | Workflow listesi periyodik |
| 7 | Repair Lab: 15sn polling doğrula | Benchmark verileri periyodik |

### TC-CROSS-005: API Hata Durumları
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Backend kapalıyken herhangi bir sayfayı aç | Hata durumu gösterilmeli (error state, retry butonu) |
| 2 | Geçersiz bir route'a git (ör. `/nonexistent`) | Next.js 404 sayfası |
| 3 | API timeout simüle et | Timeout mesajı, sayfa çökmemeli |

### TC-CROSS-006: Refine Data Provider Tutarlılığı
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | `useList` kullanan sayfaları kontrol et (Axiology, Calibrations, vb.) | Pagination URL sync çalışmalı |
| 2 | `useCustom` kullanan sayfaları kontrol et (Fleet, MCP Hub, vb.) | Custom API çağrıları doğru çalışmalı |
| 3 | `safeFetchJson` kullanan sayfaları kontrol et (Incidents, Mesh, Evolution, vb.) | Auth header + offline fallback çalışmalı |

### TC-CROSS-007: Türkçe Lokalizasyon
| Adım | İşlem | Beklenen Sonuç |
|------|-------|----------------|
| 1 | Tarih formatlarını kontrol et | `tr-TR` locale kullanılmalı (Axiology: dayjs "10 dk önce") |
| 2 | Buton etiketlerini kontrol et | Türkçe: "OTURUM AÇ", "KAYIT OL", "Kurumsal Sign-off Ver", "Uygula", "Reddet" |

---

> **Toplam Sayfa Sayısı:** 33 (+ 4 alt sayfa: learning/*, ops/*)  
> **Toplam Test Senaryosu Sayısı:** ~150+  
> **En Büyük Sayfalar:** UI Repair (73KB, 20+ tab), BilgeAPI Ops (1930 satır, 11 tab, 40+ API), Project Factory (1274 satır client)  
> **Kapsanan Test Türleri:** Fonksiyonel, CRUD, WebSocket, Polling, Auth, Filtreleme, Navigasyon, Hata Durumu, Performans, Lokalizasyon
