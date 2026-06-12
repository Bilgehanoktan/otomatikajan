# BilgeAPI PR Verification Gate Policy

Bu politika, otonom veya manuel üretilen kod yamalarının (PR drafts/revisions) doğrulama süreçlerinde uygulanacak kalite kapılarını tanımlar.

## Kurallar ve Kısıtlamalar

1. **Verification Score Modeli:** Yamalar, Sandbox doğrulama sürecinde 100 üzerinden puanlanır.
   - Puan >= 85: `REVIEW_READY`
   - Puan 70-84: `NEEDS_HUMAN_CAUTION`
   - Puan 50-69: `NEEDS_REVISION`
   - Puan < 50: `BLOCKED`
2. **Güvenlik Bypass Koruması:** `eval()`, `exec()` veya `shell=True` gibi tehlikeli kod örüntüleri saptandığında PR otomatik olarak `BLOCKED` ilan edilir.
3. **Puanlama Kriterleri:** Yama boyutu <= 50 satır olması (+10), test dosyasının varlığı (+15), rollback planı barındırması (+10) skora olumlu yansır.
