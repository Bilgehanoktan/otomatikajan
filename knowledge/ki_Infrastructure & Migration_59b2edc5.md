# Knowledge Item: Legacy Memory Migration

- **Source**: 7818a0f8-89c1-489d-8331-bd4272ea975a
- **Date**: 2026-06-19T21:55:56.883680+00:00

## Lessons Learned
- Legacy dosya taşıma işlemleri sonrası indekslerin güncellenmesi veri bütünlüğü için kritiktir.
- Taşıma süreçlerinde sistem çapında tutarlılık için indeksleme stratejileri uygulanmalıdır.

## Anti-Patterns
- {'pattern': 'Absolute Path Usage', 'description': 'Betiklerde (scripts) mutlak yolların kullanılması.', 'risk': 'Farklı ortamlarda (dev/stage/prod) betiklerin çalışmamasına ve taşınabilirlik sorunlarına yol açar.', 'remediation': 'Göreceli yollar (relative paths) veya ortam değişkenleri (environment variables) kullanılmalıdır.'}