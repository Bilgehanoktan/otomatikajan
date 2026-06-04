# Free Web API Catalog Integration Plan

## Amaç

Webden doğrudan veya backend proxy üzerinden kullanılabilecek ücretsiz ve kotasız API adaylarını sistem içinde izlenebilir bir katalog olarak sunmak.

## Kapsam

- `services/integrations/free_web_api_catalog.py` altında statik ve test edilebilir provider kataloğu.
- `services/workflow_api/free_web_api_router.py` altında `/api/v1/free-web-apis/catalog` ve provider detay endpointleri.
- `services/workflow_api/main.py` ve `libs/infra/router_registry.py` içinde aktif router kaydı.
- Unit/integration testleriyle katalog filtresi, sınırlı free tier dışlama davranışı ve OpenAPI görünürlüğü.

## Kapsam Dışı

- Üçüncü taraf API'lere otomatik yüksek hacimli canlı istek atmak.
- API key veya secret yönetimi.
- Frontend menüsüne yeni sayfa eklemek.

## Güvenlik Notları

- Katalog endpointleri secret içermez.
- Dış servis URL'leri sabittir; kullanıcı girdisiyle outbound URL oluşturulmaz.
- Sınırlı free tier kaynaklar `strict_kotasiz=true` varsayılanında dışarıda bırakılır.
