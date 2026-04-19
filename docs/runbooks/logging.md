# Egemen YAZ - Log ve Olay İzleme Runbook'u

**Sürüm:** v1.0  |  **Sahip:** EGEMEN / Platform Operations  |  **Durum:** AKTİF  |  **Son Güncelleme:** 2026-04-18  |  **Kapsam:** Mission Control, Workflow API, Event Stream, DB Logs, Trace Korelasyonu

> [!NOTE]
> **Bağlantılı Dokümanlar:** [handover_manual.md](../handover_manual.md), [ops_runbook.md](../ops_runbook.md), [global_failover_runbook.md](../global_failover_runbook.md)
> **Erişim:** Bu dokümana Mission Control paneli, Handover Manual ve Operatör Onboarding rehberlerinden link verilmiştir.

---

## 1. Amaç
Bu runbook, Egemen YAZ platformunda logların nerede görüleceğini, hangi durumda hangi kaynağa bakılacağını ve olay takibinin nasıl yapılacağını açıklar. Operatörlerin sistem sağlığını izlemesi ve hata teşhisi yapması için ana rehberdir.

## 2. Hızlı Başlangıç: Önce Nereye Bakılır

| Durum / İhtiyaç | İlk Bakılacak Yer | Kalıcı / İkincil Kaynak |
| :--- | :--- | :--- |
| **Canlı hata / anlık davranış** | Terminal / Stdout | Docker `logs -f` |
| **Kalıcı önemli olaylar / Audit** | `domain_event_logs` tablosu | Watchdog (Vektör Log) |
| **HTTP istek davranışı / Performans** | `api_metrics` tablosu | Dashboard Metrics |
| **Canlı olay akışı / Dashboard** | `/ws/events` (WebSocket) | `/api/v1/events/stream` |
| **Dağıtık trace lazım** | `trace_id` | `otel_trace` |

## 3. Ortama Göre Log Davranışı

*   **Development Ortamı (`APP_ENV=development`)**
    *   **Stdout:** İnsan okunabilir formatta basılır. Brüt debug çıktılarını izlemek için idealdir.
*   **Production Ortamı (`APP_ENV=production`)**
    *   **Stdout:** Yapılandırılmış **JSON** formatında basılır. Merkezi log toplayıcılar için optimize edilmiştir.
    *   **DB Handler:** `WARNING+` seviyesindeki loglar veritabanına (`domain_event_logs`) kalıcı olarak yazılır.
    *   **İstisnalar:** Logger `force_db=True` ile ilklendirilirse her durumda DB handler eklenir.

## 4. Log Kaynakları

### A. Konsol / Stdout
**Ne zaman bakılır:** Servis ayağa kalkmıyorsa, bağımlılık hatalarında veya anlık exception takibi sırasında.
**Karakteristik:** Production modunda JSON, geliştirme modunda metin tabanlıdır.

### B. Veritabanı Logları (`domain_event_logs`)
**Ne zaman bakılır:** Kritik olay geçmişini sorgulamak ve sistem olayları üzerinde audit yapmak için.
**Özellik:** Sadece `WARNING` ve üzeri seviyeleri hedefler. Aynı zamanda sistem sağlığı için watchdog üzerinden vektör log katmanına asenkron gönderilir.

### C. API Metrikleri (`api_metrics`)
**Ne zaman bakılır:** Endpoint bazlı performans sorunlarını tespit etmek ve hatalı istekleri gruplamak için.
**Mantık:** Hatalı isteklerde (4xx/5xx) %100, normal trafikte ~%20 örnekleme ile kaydedilir. İzleme dışı path'ler: `/health`, `/metrics`, `/static`, `/ws`, `/favicon`.

### D. Canlı Event Stream
**Ne zaman bakılır:** Mission Control dashboard üzerinden canlı operasyon izlemek için.
*   **WebSocket:** Canlı operasyon takibi ve anlık telemetri akışı için ana kanaldır.
*   **HTTP Polling:** Fallback mekanizmasıdır; testler veya harici script tüketimleri için kullanılır.

## 5. Trace ve Korelasyon Mantığı
*   Her HTTP isteğine `X-Trace-ID` atanır ve yanıt header'ında iade edilir.
*   Log satırları, DB kayıtları ve metrikler aynı `trace_id` bilgisini paylaşır.
*   Dağıtık sistem izleme (OTel) aktifse `otel_trace` korelasyonu da sağlanır.

## 6. Degraded Mode Görünürlüğü
Sistem kısıtlı kapasiteyle çalışıyorsa (degraded), response header'larından anlık sebep görülebilir:
*   `X-System-Status: degraded`
*   `X-System-Reason: database_unavailable`
*   `X-System-Reason: agent_unhealthiness`

## 7. Hızlı Teşhis Karar Ağacı
*   **Servis açılmıyor** → Önce **Stdout / Docker Logs**.
*   **Dashboard'da veri eksik** → `/api/v1/events/stream` + **Stdout**.
*   **Yanıtlar yavaş** → `api_metrics` tablosunda `response_ms` analizi.
*   **Kritik olay geçmişi** → `domain_event_logs` tablosu.
*   **Sistem kısıtlı mı?** → HTTP Response Header kontrolü.

## 8. Sık Kullanılan Komutlar

**Docker Canlı Log İzleme:**
```bash
docker compose logs -f app
docker compose logs -f worker
docker compose logs -f deerflow-worker
docker compose logs -f
```

**Kritik Olay Audit Sorgusu (SQL):**
```sql
SELECT * FROM domain_event_logs ORDER BY created_at DESC LIMIT 50;
```

**Event Stream Testi (CURL/HTTP):**
```bash
curl "http://localhost:8000/api/v1/events/stream?since_seq=0&limit=50"
```

## 9. Sınırlar ve Önemli Notlar
*   **Veri Kapsamı:** `domain_event_logs` tüm uygulama geçmişini içermez; önemli olaylar (WARNING+) filtresidir.
*   **Tam Kronoloji:** Eksiksiz bir kronoloji takibi için **Stdout**, **Event Stream** ve **Api_Metrics** verileri konfigüre edilmeli ve birlikte değerlendirilmelidir.
*   **Recap:** Log yazım davranışı, logger ilklendirme parametrelerine ve `APP_ENV` değerine sıkı sıkıya bağlıdır.

## 10. Operasyonel Özet
"İlk teşhis eylemi her zaman **stdout** üzerinden terminalden başlar. Kalıcı teyit ve geçmiş analizi **DB** loglarından alınır. Performans takibi **api_metrics**’ten, canlı saha operasyonu izleme ise **event stream** üzerinden yürütülür."
