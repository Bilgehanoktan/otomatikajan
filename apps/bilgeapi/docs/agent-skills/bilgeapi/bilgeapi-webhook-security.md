# BilgeAPI Webhook Security Policy

Bu politika, BilgeAPI'nin dış sistemlerle entegre olurken (webhook dispatch) uyması gereken SSRF korumaları ve ağ güvenliği kurallarını belirler.

## Kurallar ve Kısıtlamalar

1. **Ağ Sınırları ve SSRF Koruması:** Webhook çağrıları kesinlikle özel (private) IP adreslerine, localhost'a veya yerel ağ servislerine (`127.0.0.1`, `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x`) istek atamaz.
2. **Host Allowlist:** Webhook gönderimleri sadece önceden doğrulanmış ve allowlist'e eklenmiş host adreslerine yapılabilir.
3. **İmza Doğrulama (HMAC):** Giden tüm webhook istekleri, alıcı tarafın doğrulaması için `BILGEAPI_WEBHOOK_SECRET` kullanılarak HMAC SHA-256 ile imzalanmalıdır.
4. **Timeout ve Hata Yönetimi:** Webhook istekleri için maksimum zaman aşımı (timeout) 5 saniye olarak sınırlandırılmalıdır.
