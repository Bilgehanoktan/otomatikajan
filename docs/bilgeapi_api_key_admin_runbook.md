# BilgeAPI API Key Admin Runbook

Bu runbook, DB-backed BilgeAPI API key lifecycle islemlerini CLI ve HTTP API uzerinden guvenli sekilde yonetmek icindir.

## Gereksinimler

- Admin veya `SOVEREIGN_PRIME` role sahip bir mevcut API key.
- BilgeAPI base URL: varsayilan `http://127.0.0.1:8100`.
- Plaintext key degeri yalnizca olusturma cevabinda gorunur; daha sonra geri getirilemez.

## Key Olusturma

```powershell
py -3.13 scripts\bilgeapi_api_key_admin.py --admin-api-key <ADMIN_KEY> create --role OPERATOR --tenant-id tenant-alpha --description "worker key"
```

Kisa wrapper:

```powershell
py -3.13 scripts\bilgeapi_create_api_key.py --admin-api-key <ADMIN_KEY> --role OPERATOR --tenant-id tenant-alpha --description "worker key"
```

Response icindeki `plaintext_key` hemen secrets manager'a kaydedilmelidir. Log, ticket veya dokumana yapistirilmaz.

## Key Listeleme

```powershell
py -3.13 scripts\bilgeapi_api_key_admin.py --admin-api-key <ADMIN_KEY> list
```

Listeleme cevabi `plaintext_key` veya `key_hash` dondurmez; yalnizca `key_fingerprint`, `key_prefix`, `role`, `tenant_id`, quota ve lifecycle metadata dondurur.

## Key Iptal Etme

```powershell
py -3.13 scripts\bilgeapi_api_key_admin.py --admin-api-key <ADMIN_KEY> revoke --key-id key_123 --reason "rotation"
```

Kisa wrapper:

```powershell
py -3.13 scripts\bilgeapi_revoke_api_key.py --admin-api-key <ADMIN_KEY> --key-id key_123 --reason "rotation"
```

Revoked veya expired key ile yapilan istekler `401 Unauthorized` donmelidir.

## Quota Guncelleme

```powershell
py -3.13 scripts\bilgeapi_api_key_admin.py --admin-api-key <ADMIN_KEY> quota --key-id key_123 --quota-daily 1000 --quota-monthly 30000
```

Quota usage:

```powershell
py -3.13 scripts\bilgeapi_api_key_admin.py --admin-api-key <ADMIN_KEY> quota-usage --key-id key_123
```

## Guvenlik Kurallari

- Production ortaminda plaintext `BILGEAPI_STATIC_KEYS` fallback kapali kalmalidir.
- `BILGEAPI_STATIC_KEY_HASHES` veya DB-backed API key kullanilmalidir.
- `/metrics` endpoint'i production/private modda sadece admin yetkisiyle acilmalidir.
- `tenant_id` operator tarafindan spoof edilmemeli; DB-backed key veya JWT claim gibi guvenilir kaynaklardan alinmalidir.
