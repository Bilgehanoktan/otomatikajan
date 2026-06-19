# Knowledge Item: Legacy Memory Migration

- **Source**: f13cc954-c2e1-40bc-99e9-56aa6a6436f6
- **Date**: 2026-06-18T21:27:57.298305+00:00

## Lessons Learned
- Büyük dosyalardan kaçının, birçok küçük dosya kullanın
- Hataları her düzeyde eksiksiz bir şekilde ele alın
- Giriş verileri sistem sınırlarında всегда doğrulanmalıdır
- Mutasyondan kaçının, bunun yerine immutable desenleri kullanın

## Anti-Patterns
- Mutasyon kullanmak (değişken nesnelerin kullanılması)
- Scriptlerde mutlak yollar kullanmak
- Hataları sessizce yutmak
- Dış veriler (kullanıcı girişi, API yanıtları, dosya içeriği) güvenmek