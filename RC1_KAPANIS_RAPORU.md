# RC1 Kapanış Raporu

Bu sürümde yapılan ana düzeltmeler:

## Kapatılan kritik sorunlar
- `api/task_router.py` compatibility shim güçlendirildi.
  - `TaskCreateRequest`, `TaskUpdateRequest`, `_project_to_dict` re-export ediliyor.
  - read/write/control router'ları tek shim altında toplanıyor.
- `llm/cost_tracker.py` düzeltildi.
  - Hatalı `cost_summary` import sorunu kapatıldı.
  - Tanımsız `_calc_cost` çağrısı kaldırıldı.
  - Saf hesaplama `llm.cost_calc.calculate_cost()` üzerinden yapılıyor.
- `llm/cost_calc.py` içine legacy uyumluluk için `cost_summary()` eklendi.
- `memory/store.py` yeniden düzenlendi.
  - Ağır importlar lazy hale getirildi.
  - `AsyncSession` NameError kapatıldı.
  - `numpy` import kullanımı düzeltildi.
  - `_cosine_sim` ve `_mmr` DB'den bağımsız çalışır hale getirildi.
- `core/heal_engine.py` davranışı legacy test beklentisiyle hizalandı.
  - Çok düşük skor ilk kontrolde `DEGRADED`, sonraki kontrolde `ISOLATED` akışına uydu.
- `tasks/celery_app.py` içine Celery yoksa çalışan minimal fallback eklendi.
- `tests/conftest.py` sadeleştirildi ve tekrar eden stub blokları kaldırıldı.
  - Yalnızca eksik opsiyonel paketlerde stub enjekte ediyor.
  - Celery/Telegram stub'ları eklendi.

## Son durum
- Faz 10/11/12 ve RC1 özel testleri geçti.
- Önceden kırık olan cost tracker, memory store ve heal engine uyumsuzlukları giderildi.
- Repo paketi temizlendi (`.pytest_cache` çıkarıldı).

## Not
Gerçek uygulama çalışması için üretim bağımlılıkları yine gereklidir:
- FastAPI
- SQLAlchemy
- bcrypt
- httpx
- (opsiyonel) Celery, Redis, Telegram

Celery olmayan geliştirme/test ortamlarında artık import-time çöküş yaşanmaz.
