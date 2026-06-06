# API Key Admin CLI Operations Verification — BilgeAPI Phase 17

Bu doküman, DB-backed API key lifecycle yönetim işlemlerinin CLI araçları üzerinden başarıyla gerçekleştirildiğini kanıtlayan çalışma raporudur.

---

## 1. Operasyon Adımları ve Çıktılar

### A. Key Listeleme (List) - Boş Durum
İlk olarak veritabanında kayıtlı anahtar olmadığı doğrulandı:

```powershell
python scripts/bilgeapi_api_key_admin.py --admin-api-key dev-test-key-001 list
```

**Çıktı:**
```json
[]
```

---

### B. Yeni API Key Oluşturma (Create)
`OPERATOR` rolünde, `tenant-alpha` tenant'ına bağlı yeni bir API key oluşturuldu:

```powershell
python scripts/bilgeapi_create_api_key.py --admin-api-key dev-test-key-001 --role OPERATOR --tenant-id tenant-alpha --description "worker key"
```

**Çıktı:**
```text
Plaintext key is shown once. Store it in a secrets manager now.
{
  "id": "key_cc8c1e5b",
  "key_prefix": "blg_live_",
  "key_fingerprint": "1f3891a6762f",
  "role": "OPERATOR",
  "description": "worker key",
  "tenant_id": "tenant-alpha",
  "is_active": true,
  "created_by": "api_key_f9dc6e1a25f1",
  "revoked_by": null,
  "revoke_reason": null,
  "created_at": "2026-06-06T07:48:59.158711Z",
  "expires_at": null,
  "revoked_at": null,
  "last_used_at": null,
  "quota_daily": null,
  "quota_monthly": null,
  "plaintext_key": "blg_live_ToYW1...[REDACTED]"
}
```

---

### C. Kota Limiti Atama (Quota Update)
Oluşturulan anahtara günlük 50, aylık 1500 limit atandı:

```powershell
python scripts/bilgeapi_api_key_admin.py --admin-api-key dev-test-key-001 quota --key-id key_cc8c1e5b --quota-daily 50 --quota-monthly 1500
```

**Çıktı:**
```json
{
  "id": "key_cc8c1e5b",
  "key_prefix": "blg_live_",
  "key_fingerprint": "1f3891a6762f",
  "role": "OPERATOR",
  "description": "worker key",
  "tenant_id": "tenant-alpha",
  "is_active": true,
  "created_by": "api_key_f9dc6e1a25f1",
  "revoked_by": null,
  "revoke_reason": null,
  "created_at": "2026-06-06T07:48:59.158711Z",
  "expires_at": null,
  "revoked_at": null,
  "last_used_at": null,
  "quota_daily": 50,
  "quota_monthly": 1500
}
```

---

### D. Kota Kullanım Durumu (Quota Usage)
İlk durum sorgulandı (kullanım: 0):

```powershell
python scripts/bilgeapi_api_key_admin.py --admin-api-key dev-test-key-001 quota-usage --key-id key_cc8c1e5b
```

**Çıktı:**
```json
{
  "key_id": "key_cc8c1e5b",
  "quota_daily": 50,
  "quota_monthly": 1500,
  "daily_used": 0,
  "monthly_used": 0,
  "daily_remaining": 50,
  "monthly_remaining": 1500
}
```

---

### E. İstek Gönderme & Kota Artışı Doğrulaması
Oluşturulan DB-backed API key ile istek atılarak quota tüketimi doğrulandı:

```powershell
python scripts/bilgeapi_live_smoke.py --base-url http://127.0.0.1:8100 --api-key [REDACTED_SECRET]
```

İstek sonrası kota kullanımının arttığı teyit edildi:
```json
{
  "key_id": "key_cc8c1e5b",
  "quota_daily": 50,
  "quota_monthly": 1500,
  "daily_used": 1,
  "monthly_used": 1,
  "daily_remaining": 49,
  "monthly_remaining": 1499
}
```

---

### F. API Key İptali (Revocation)
rotation sebebiyle key pasife alındı:

```powershell
python scripts/bilgeapi_revoke_api_key.py --admin-api-key dev-test-key-001 --key-id key_cc8c1e5b --reason "rotation"
```

**Çıktı:**
```json
{
  "id": "key_cc8c1e5b",
  "is_active": false,
  "revoked_by": "api_key_f9dc6e1a25f1",
  "revoke_reason": "rotation",
  "revoked_at": "2026-06-06T07:49:29.847578Z"
}
```

İptal edilen key ile yapılan sonraki live smoke isteği `HTTP 401` hatasıyla başarıyla engellendi:
```json
{"detail": "Unauthorized: Invalid API key"}
```

---

## 2. Genel Sonuç
- **Durum**: **PASSED** ✅
- **Yorum**: DB-backed API Key Lifecycle, Quota Enforcement ve Revocation akışları CLI araçlarıyla uçtan uca doğrulanmıştır.
