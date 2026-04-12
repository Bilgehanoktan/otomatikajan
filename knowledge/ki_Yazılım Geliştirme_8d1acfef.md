# Knowledge Item: Güvenlik ve Performans Önerileri

- **Source**: a3d280aa-c0de-4d52-8a87-c70979f270c1
- **Date**: 2026-04-12T06:29:53.818940+00:00

## Lessons Learned
- Kullanıcı girdilerini sempre parametrelerle bağlayın
- Hataları logging ile kaydedin ve yönetin
- Sorgularınızı pagination ile sınırlandırın
- Connection pool kullanın
- Loglama yapın
- Tüm fonksiyonları test edin ve edge case'leri düşünün
- Docstring'ler ekleyin

## Anti-Patterns
- SQL injection'a açık olmak
- Hata yönetimini ihmal etmek
- Güvensiz deserialization kullanmak
- Hardcoded secret kullanmak
- N+1 query problemi yaşamak
- Connection'ları açıp kapatmak yerine connection pool kullanmamak
- Loglama yapılmaması
- Test kapsamı yetersiz olmak
- Type hint'ler olmadan kod yazmak