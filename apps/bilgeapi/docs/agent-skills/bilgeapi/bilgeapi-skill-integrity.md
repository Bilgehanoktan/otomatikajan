# BilgeAPI Skill Integrity Policy

Bu politika, otonom yeteneklerin ve politikaların bütünlüğünü (integrity) doğrulamak için uygulanan kural ve standartları tanımlar.

## Kurallar ve Kısıtlamalar

1. **Hash Manifest Doğrulaması:** Tüm `SKILL.md` ve politika dosyaları startup aşamasında SHA-256 algoritmasıyla taranır ve hash manifesti ile eşleştirilir.
2. **Kataloğun Korunması:** Hash'i doğrulanmayan veya allowlist dışındaki hiçbir yetenek / markdown dosyası runtime'da verified cache'e alınmaz ve servis edilmez.
3. **Değiştirilemezlik:** Çalışma zamanında (runtime) diskteki markdown dosyalarının modifiye edilmesi durumunda sistem alarm üretir ve catalog endpoint'lerini servis dışı bırakır.
