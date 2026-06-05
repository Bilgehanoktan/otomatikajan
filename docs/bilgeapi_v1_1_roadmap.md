# BilgeAPI v1.1 Roadmap & Architecture Planning

Bu doküman, BilgeAPI'nin v1.0.0 Production Release-Stable sürümü sonrasında gelecek olan **v1.1** sürümü için planlanan mimari genişletmeleri, teknik gereksinimleri ve özelliklerin önceliklendirme matrisini içerir.

---

## 1. Planlanan v1.1 Özellikleri

### 1. Multi-tenant Workspace Modeli
- **Açıklama**: Tek bir BilgeAPI kurulumu üzerinde birden fazla bağımsız takımın veya şirketin (tenant) çalışabilmesini sağlayan mantıksal veri izolasyonu.
- **Teknik Kapsam**:
  - `workspace` ve `tenant` veri tabanı tablolarının tasarımı.
  - API isteklerinde workspace bazlı izolasyonu zorunlu kılacak `Workspace-Context` middleware entegrasyonu.
  - Veri tabanı sorgularında otomatik tenant filtreleme (Soft Isolation).

### 2. API Key Database Storage & Hash Migration
- **Açıklama**: Statik ortam dosyalarındaki API anahtarlarının veritabanına taşınması ve yönetim arayüzü (Admin API) üzerinden dinamik olarak üretilmesi/silinmesi.
- **Teknik Kapsam**:
  - `api_keys` tablosunun tasarımı (id, tenant_id, key_hash, role, description, created_at, expires_at, is_active).
  - Mevcut `.env` içindeki key'leri sıfır kesintiyle veritabanına taşıyacak tek seferlik Alembic veri göçü (data migration) scripti.
  - Dinamik key doğrulaması için DB caching katmanı (Redis LRU cache).

### 3. Redis-backed Dynamic Usage Quotas
- **Açıklama**: Tenant veya API key bazında saniyelik rate limitlerin (RPS) ötesinde, günlük/aylık istek kotalarının dinamik olarak yönetilmesi.
- **Teknik Kapsam**:
  - Redis üzerinde pencere bazlı (sliding window) kota takibi (`quota:tenant_id:daily`, `quota:tenant_id:monthly`).
  - Kota sınırına yaklaşıldığında (örn: %80 ve %100) Slack/Teams üzerinden uyarı gönderen event-driven mekanizma.
  - Kota aşımında `429 Too Many Requests` (Quota Exceeded) hatasıyla koruma katmanı.

### 4. Durable Queue Worker Dashboard
- **Açıklama**: Faz 12'de entegre edilen `BILGEAPI_DURABLE_QUEUE_ENABLED` arka plan işlerinin (webhook delivery ve retries) görsel olarak izlenmesi, başarısız olanların elle yeniden tetiklenmesi.
- **Teknik Kapsam**:
  - Celery Flower benzeri, BilgeAPI kontrol paneline entegre hafif bir iş izleme paneli (Worker Dashboard UI).
  - Kuyruktaki bekleyen, işlenen, hata alan ve dead-letter queue'ya (DLQ) düşen görevlerin metrik ve log takibi.

### 5. Slack Block Kit & MS Teams Adaptive Cards Entegrasyonu
- **Açıklama**: Faz 12'deki düz metin (markdown) bildirimlerin yerine, interaktif butonlar ve detaylı zengin içerik barındıran kart tasarımlarının eklenmesi.
- **Teknik Kapsam**:
  - `SlackAdapter` için Block Kit JSON şemalarının entegrasyonu.
  - `TeamsAdapter` için Adaptive Cards 1.4+ standartlarında mesaj adaptasyon şablonları.
  - Bildirim kartları üzerinden "Onayla / Reddet" aksiyonlarının doğrudan Slack/Teams arayüzünden tetiklenmesi (Interactive Webhook Endpoints).

### 6. Tenant Bazlı Audit & Reporting
- **Açıklama**: Kurumsal müşterilerin kendi sistem aktivitelerini, audit loglarını ve hata oranlarını bağımsız olarak sorgulayabileceği ve indirebileceği raporlama altyapısı.
- **Teknik Kapsam**:
  - `AuditEvent` sorgularının tenant bazında filtrelenerek JSON/CSV formatında export edilmesi.
  - Günlük/Haftalık performans ve hata trendi raporlarının otomatik oluşturularak e-posta veya webhook ile ulaştırılması.

### 7. Usage Metering Dashboard
- **Açıklama**: Operatörlerin ve sistem yöneticilerinin hangi tenant'ın ne kadar kaynak (istek sayısı, CPU süresi, diagnostic maliyeti) tükettiğini görebileceği finansal/operasyonel izleme paneli.
- **Teknik Kapsam**:
  - Prometheus/Grafana panellerinin BilgeAPI Admin UI içine gömülmesi (embedded charts).
  - Aylık bütçe ve kullanım öngörüsü (forecasting) göstergeleri.

---

## 2. Risk / Efor / Değer Matrisi

Özelliklerin geliştirme sıralamasını belirlemek amacıyla kullanılan analiz tablosu:

| Özellik | Değer (Value) | Geliştirme Eforu (Effort) | Teknik Risk (Risk) | Öncelik Skoru (ROI) |
| :--- | :--- | :--- | :--- | :--- |
| **1. API Key DB Storage & Migration** | Yüksek | Düşük | Düşük | **Çok Yüksek** |
| **2. Redis-backed Usage Quota** | Yüksek | Orta | Orta | **Yüksek** |
| **3. Slack Block Kit & Teams Cards** | Orta | Düşük | Düşük | **Yüksek** |
| **4. Multi-tenant Workspace Modeli** | Çok Yüksek | Yüksek | Yüksek | **Orta** |
| **5. Tenant Bazlı Audit & Reporting** | Orta | Orta | Düşük | **Orta** |
| **6. Usage Metering Dashboard** | Orta | Orta | Düşük | **Orta** |
| **7. Durable Queue Dashboard** | Düşük | Orta | Orta | **Düşük** |

> [!NOTE]
> **Öncelik Skoru Hesabı**: Değer / (Efor + Risk) formülü göz önüne alınarak hesaplanmıştır. Eforu düşük, teknik riski az ve iş değeri yüksek özellikler ilk sıralara yerleştirilmiştir.

---

## 3. v1.1 Release Planlama

Yukarıdaki matrise dayanarak v1.1 ve v1.2 sürümlerinin kapsamı şu şekilde belirlenmiştir:

### 🚀 v1.1 Sürüm Kapsamı (Q3 - Kısa Vadeli)
1. **API Key Database Storage & Hash Migration**: Güvenlik açığı riskini sıfıra indirmek ve dinamik yönetim sağlamak amacıyla önceliklidir.
2. **Redis-backed Dynamic Usage Quotas**: Altyapısı hazır olan rate limit modülünün kota katmanıyla genişletilmesidir.
3. **Slack Block Kit & MS Teams Adaptive Cards**: Operasyonel interaktiviteyi artırmak için düşük eforlu yüksek kazanım sunar.

### 🗺️ v1.2 Sürüm Kapsamı (Q4 - Orta Vadeli)
1. **Multi-tenant Workspace Modeli**: Büyük mimari refactoring ve veri izolasyon katmanı gerektirdiği için v1.2'ye planlanmıştır.
2. **Tenant Bazlı Audit & Reporting** & **Usage Metering Dashboard**: Workspace modeli tamamlandıktan sonra üstüne inşa edilecektir.
3. **Durable Queue Worker Dashboard**: Operasyonel kolaylık sağlayan izleme aracı olarak en son aşamaya bırakılmıştır.
