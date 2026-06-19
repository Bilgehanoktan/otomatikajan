# Knowledge Item: Legacy Memory Migration

- **Source**: be52c5cd-51ff-479c-be42-1be7226d2938
- **Date**: 2026-06-12T19:07:49.963164+00:00

## Lessons Learned
- Legacy dosyaların taşınması ve indeks güncellemeleri eş zamanlı yönetilmelidir.
- Veri migrasyonu sonrası indeks doğrulama adımı başarı kriteri olarak tanımlanmalıdır.

## Anti-Patterns
- {'pattern': 'Absolute Path Usage', 'description': 'Scriptler içerisinde mutlak dosya yolları (absolute paths) kullanmak.', 'risk': 'Sistemin farklı ortamlarda (dev, staging, prod) çalışmamasına ve taşınabilirlik sorunlarına yol açar.', 'remedy': 'Relatif yollar veya çevre değişkenleri (environment variables) kullanılmalıdır.'}