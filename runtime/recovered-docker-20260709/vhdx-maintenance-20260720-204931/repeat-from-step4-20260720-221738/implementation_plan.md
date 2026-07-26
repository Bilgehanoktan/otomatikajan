# Docker VHDX Compact Tekrar Plani

## Kapsam

Onceki bakim planinin 4. adimindan itibaren `Optimize-VHD -Mode Full`
islemini tekrar uygula ve ardindan tum runtime/veri kontrollerini yenile.

## Guvenlik Onkosullari

1. Ilk basarili `compact-result.json` kanitini degistirme.
2. Compact baslamadan once guncel PostgreSQL ve Redis yedegi al.
3. Compose, Docker Desktop ve WSL'i kontrollu durdur.
4. Aktif VHDX'in exclusive-open kontrolunu yap.
5. Unsafe compact secenegi kullanma.

## Uygulama ve Dogrulama

1. Elevated `Optimize-VHD -Mode Full` calistir.
2. VHDX byte farkini kaydet.
3. Docker Desktop ve full Compose stack'i yeniden baslat.
4. PostgreSQL/Redis kalicilik baseline'ini karsilastir.
5. HTTP, worker, migration, Telegram configuration ve log gate'lerini test et.
6. EpisodeRecord/ActionRecord ve tekrar raporunu kaydet.

## Rollback

- Bu tekrar icin alinacak PostgreSQL custom dump ve Redis RDB kullanilir.
- Compact baslamadan once hata olursa VHDX degistirilmeden stack yeniden
  baslatilir.
- Veri mismatch durumunda servisler durdurulur ve yedekler korunur.

## Uygulama Sonucu

- Guncel logical backups: `COMPLETED`
- Controlled shutdown ve exclusive-open: `COMPLETED`
- Elevated `Optimize-VHD -Mode Full`: `COMPLETED`
- Ek reclaimed alan: `0` bytes; VHDX zaten compact durumda
- Docker ve full Compose restart: `COMPLETED`
- Persistence/runtime/log verification: `COMPLETED`
- Host regression tests: `20/20 passed`
- Traceability kaydi: `COMPLETED`
- Genel sonuc: `SUCCESS`
