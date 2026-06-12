# BilgeAPI Audit Ledger Policy

Bu politika, sistemde yapılan tüm otonom değişikliklerin ve verifikasyon kontrollerinin izlenebilirlik (traceability) standartlarını belirler.

## Kurallar ve Kısıtlamalar

1. **Değiştirilemez Günlük Kaydı:** Yapılan her eylem ve her güvenlik geçidi kontrolü Review Ledger sistemine SHA-256 hash zinciriyle (`hash_chain`) kaydedilmelidir.
2. **Kritik Olay Tipleri:** Aşağıdaki olay tipleri her check adımında ledger'a yazılmalıdır:
   - `SKILL_CATALOG_LOADED`
   - `SKILL_HASH_VERIFIED`
   - `SKILL_CHECK_APPLIED`
   - `SKILL_CHECK_FAILED`
   - `SKILL_POLICY_BLOCKED`
3. **Secret Maskeleme:** Kaydedilen event payload'ları içinde hiçbir api_key, token, password veya PII (Kişisel Veri) yer almamalı; redaction filtrelerinden geçirilmelidir.
