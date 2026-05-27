# Knowledge Item: Self Repair Case: INC-CEO-4014090CFB31

- **Source**: 7a68f213-71d8-4d48-9e23-3edaa6e33c6f
- **Date**: 2026-05-25T10:56:51.898528+00:00

## Lessons Learned
- Değişmezlik luôn ön planda tutulmalıdır. Mevcut nesneleri değiştirmek yerine yeni nesneler oluşturulmalıdır.
- Dosya organizasyonu_many küçük dosya yerine birkaç büyük dosya kullanmaktan kaçınılmalıdır.
- Hata işleme her düzeyde eksiksiz bir şekilde yapılmalıdır.
- Giriş verileri her zaman sistem sınırlarında doğrulanmalıdır.

## Anti-Patterns
- Mevcut nesneleri değiştirmek (mutate)
- Büyük dosyalar kullanmak
- Hataları görmezden gelmek veya örtbas etmek
- Giriş verilerini doğrulamadan işleme almak
- Derin iç içe yapılar kullanmak