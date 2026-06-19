# Sovereign AGI Mimari Standartlar ve Geliştirme Manifestosu

Bu manifesto; proje genelinde sıklıkla karşılaşılan Docker çevre uyuşmazlıkları, Pydantic sürüm geçişleri, arayüz kontrast kayıpları ve işletim sistemi tabanlı kodlama hatalarını kalıcı olarak engellemek amacıyla oluşturulmuş **bağlayıcı bir standartlar bütünüdür.** 

Bu repoda çalışan tüm yapay zeka ajanları (Agents) ve insan geliştiriciler (Operators), yapacakları tüm geliştirmelerde buradaki kurallara **istisnasız uymakla yükümlüdür.**

---

## 🛠️ 1. Docker Çevre Tutarlılığı ve Geliştirme Standartları (P1)

Konteyner tabanlı sistemlerin yerel geliştirme süreçlerinde host (ana bilgisayar) üzerindeki kod değişiklikleriyle anlık senkronize olması zorunludur.

> [!IMPORTANT]
> - **Geliştirme Ortamında Hacim Bağlama (Volumes)**: Geliştirme aşamasında kullanılan tüm servislerde (Next.js, Python FastAPI, Celery Workers vb.) yerel diskteki güncel kodların konteyner içine yansıması için `volumes` bağlaması bulunmalıdır.
> - **CMS ve Statik Servisler**: Arayüzü sunan `cms` gibi `next start` veya `npm run start` modunda çalışan servisler yerel volume bağlaması barındırmıyorsa veya izole çalışıyorsa; en ufak kod değişikliğinde Docker imajı **mutlaka yeniden inşa edilmelidir** (`docker compose build <service_name>`).
> - **Docker Sağlık Kontrolleri (Healthchecks)**: Tüm kritik konteynerler (`app`, `db`, `redis`, `deerflow-bridge`) için `docker-compose.yml` içinde kararlı ve hafif `healthcheck` tanımları yapılmalı, bağımlı servisler `condition: service_healthy` ile başlatılmalıdır.

---

## 🐍 2. Modern Python Tip Güvenliği ve Pydantic v2 Uyumluluğu (P1)

Pydantic v2 sürümünün getirdiği katı tip ve doğrulama kısıtlamaları altındaki backend kararlılığı korunmalıdır.

> [!CAUTION]
> - **Legacy Typings Yasaklanmıştır**: Query parametrelerinde ve FastAPI endpoints üzerinde `from typing import Optional` gibi v1 tarzı generic tiplerin kullanımı yasaktır. 
> - **Modern Union Tipler**: Bunun yerine modern Python `T | None` standardı kullanılmalı ve varsayılan değerler açıkça tanımlanmalıdır (örn: `Query(None)`).
> - **TypeAdapter Geçişleri**: Dinamik JSON şeması doğrularken veya API veri eşleşmelerinde doğrudan v1 `TypeAdapter` yerine, v2 `pydantic.TypeAdapter` kullanılmalı ve `ForwardRef` çözümleri mutlaka asenkron olarak güvenli ele alınmalıdır.

```python
# ❌ YANLIŞ (Pydantic v2 altında runtime hatasına sebep olabilir)
from typing import Optional
from fastapi import Query

@router.get("/items")
def read_items(limit: Optional[int] = Query(None)):
    ...

#  DOĞRU (100% Kararlı ve Pydantic v2 Uyumlu)
from fastapi import Query

@router.get("/items")
def read_items(limit: int | None = Query(None)):
    ...
```

---

## 🎨 3. UI Kontrast, Tema ve CSS Tokenizasyon Kuralları (P2)

Sovereign AGI premium neon-mavi koyu teması, yüksek okunabilirlik ve kusursuz görsel hiyerarşi standartlarını korumalıdır.

> [!WARNING]
> - **Hardcoded Renk Kullanımı Kesinlikle Yasaktır**: React bileşenleri veya Vanilla CSS sınıfları içinde asla `#ffffff`, `#f9f9f9` veya `bg-white` gibi sabit, açık tema renk kodları doğrudan yazılmamalıdır.
> - **CSS Değişkenleri (Tokens)**: Tüm renkler, yerleşimler ve geçişler projenin global CSS değişkenleri (`var(--background)`, `var(--bg-panel)`, `var(--foreground)`, `var(--primary)`) üzerinden beslenmelidir.
> - **Karanlık Tema Kontrastı**: Eklenen tüm yeni HUD panelleri, veri tabloları (`custom-table`) ve pre/code blokları koyu tema kılavuz çizgileriyle (`border-white/5`) ve şeffaf koyu cam kart efektleriyle (`rgba(255, 255, 255, 0.03)`) görsel olarak uyumlu ve yüksek kontrastlı olmalıdır.

---

## 🖥️ 4. İşletim Sisteminden Bağımsız Çıktı Kararlılığı (Unicode Terminal Safety) (P2)

Otomasyon ve test scriptlerinin, Windows cmd/powershell de dahil olmak üzere her işletim sisteminde unicode karakterleri çökmeden basabilmesi gerekir.

> [!TIP]
> - **Çıktı Kodlamasını Zorla UTF-8 Yapın**: Yazılan tüm konsol scriptlerinin giriş noktasına (main fonksiyonu) terminal çıktı kodlamasını güvenli bir şekilde `utf-8` olarak rekonfigüre eden koruma bloğu eklenmelidir.
> - **Batch Script Desteği**: Terminal bazlı `.bat` veya `.sh` scriptlerinde `PYTHONIOENCODING=utf-8` çevre değişkeni her zaman önceden tanımlanmalıdır.

```python
import sys

def main():
    # Terminal unicode ve türkçe karakter çökme koruması
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("🚀 Sistem Durumu: Nominal (▶ ACTIVE)")
```

---

## 📊 5. DOM Hiyerarşi Doğrulamalı E2E Test Standartları (P3)

Arayüz testleri sadece sayfaların yüklenmesini değil, bileşenlerin mantıksal yerleşimini de doğrulamalıdır.

* **Yapısal Doğrulama**: Playwright duman (smoke) testleri, sadece `200 OK` durum kodlarını kontrol etmekle kalmamalı; sidebar gibi kritik bileşenlerde parent/child ağacının DOM üzerinde doğru gruplarda render edildiğini hiyerarşik olarak teyit etmelidir.
* **WebSocket Otomatik Kurtarma**: Tüm gerçek zamanlı (real-time) HUD sayfalarında, Playwright düzeyinde WebSocket kesinti simülasyonları (`tests/ui_repair/test_websocket_reconnect.py`) standart olarak koşulmalı; bağlantı koptuğunda arayüzün kararlı bir şekilde degrade moduna geçmesi ve bağlantı geldiğinde otomatik olarak senkronize olması garanti edilmelidir.

---

Bu standartlara uygun şekilde geliştirilen kodlar, projenin **otonom evrim sürecindeki en büyük güvencesidir.**
