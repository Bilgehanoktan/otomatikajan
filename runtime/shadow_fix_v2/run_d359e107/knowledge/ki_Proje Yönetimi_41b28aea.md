# Knowledge Item: Legacy Memory Migration

- **Source**: 1195b71c-de71-4b68-bcb2-84f556b5e7a0
- **Date**: 2026-06-12T21:55:06.059023+00:00

## Lessons Learned
- Tüm projelerde mutlak yollar (absolute paths) yerine göreceli yollar (relative paths) kullanmak
- Dosya migration işlemlerinin düzenli olarak test edilmesi ve güncellenmesi
- Projede kullanılan tüm scriptlerin düzenli olarak gözden geçirilmesi ve güncellenmesi

## Anti-Patterns
- Mutlak yolların (absolute paths) kullanılmaması
- Scriptlerde sabit değerlerin (hardcoded values) kullanılmaması
- Hataların yeterli ayrıntı ile kayıt altına alınmaması (insufficient error logging)