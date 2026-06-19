# Knowledge Item: Legacy Memory Migration

- **Source**: 95d11a3f-5a8d-4d17-923f-e57b300f1ecc
- **Date**: 2026-06-18T21:27:59.269326+00:00

## Lessons Learned
- Mevcut veri dosyalarınınMigration işlemlerinde dikkatli olunmalıdır.
- Dosya yolundaki değişikliklerin sisteme etkisi değerlendirilmelidir.
- Güncellenen endekslerin doğruluğu kontrol edilmelidir.
- Proje boyunca yapılan değişikliklerin dökümünün tutulması önemlidir.

## Anti-Patterns
- Mutlak yol kullanımlarından kaçının.
- Dosya isimlerinde ve yolunda değişkenlerin kullanımı tercih edilmelidir.
- Geliştirme sırasında绝对 yol kullanımını azaltmak için config dosyaları veya environment değişkenleri kullanılabilir.