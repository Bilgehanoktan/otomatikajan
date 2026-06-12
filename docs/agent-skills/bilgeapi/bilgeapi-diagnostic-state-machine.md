# BilgeAPI Diagnostic State Machine Policy

Bu politika, diagnostik iş akışlarının durum geçişlerindeki (state transitions) kısıtlamaları ve izlenebilirlik kurallarını belirler.

## Kurallar ve Kısıtlamalar

1. **Geri Dönülemez Final Durumlar:** Diagnostik süreci bir kere `COMPLETED` veya `FAILED` (final state) konumuna ulaştığında, tekrar `RUNNING` veya `QUEUED` durumuna geçirilemez.
2. **Audit Trail Zorunluluğu:** Her durum geçişi (örn: `QUEUED` -> `RUNNING`) veritabanına ve Audit Ledger sistemine anında kaydedilmelidir.
3. **Idempotency Check:** Tüm otonom tetiklemeler ve diagnostik çağrıları, çifte çalıştırmayı (double execution) önlemek amacıyla benzersiz bir `idempotency_key` ile yürütülmelidir.
