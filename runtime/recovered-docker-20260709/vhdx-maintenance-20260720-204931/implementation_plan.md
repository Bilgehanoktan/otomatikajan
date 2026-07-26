# Docker VHDX Compact Bakim Plani

## Hedef

Aktif Docker Desktop VHDX'i `--allow-unsafe` kullanmadan Windows
`Optimize-VHD -Mode Full` ile compact etmek; PostgreSQL, Redis ve Compose
durumunun korundugunu kanitlamak.

## On Kosullar

1. `docker_data.vhdx` dosyasinin aktif Docker Desktop store oldugunu dogrula.
2. Compose health, PostgreSQL count, Redis key count ve quarantine uzunlugunu
   kaydet.
3. Guncel PostgreSQL custom-format dump ve Redis `dump.rdb` yedegi olustur.
4. Docker durdurulmadan once SHA256 hash'lerini kaydet.

## Uygulama

1. Compose stack'i sinirli grace period ile durdur.
2. Docker Desktop'i kapat ve `wsl --shutdown` calistir.
3. Docker Desktop ve WSL process'lerinin VHDX'i tutmadigini dogrula.
4. Exact active VHDX path'e elevated `Optimize-VHD -Mode Full` uygula.
5. `--allow-unsafe` iceren hicbir komut calistirma.

## Dogrulama

1. Compact oncesi ve sonrasi fiziksel VHDX boyutlarini karsilastir.
2. Docker Desktop'i baslat ve `docker info` icin bekle.
3. Compose stack'i `--no-build --wait` ile baslat.
4. PostgreSQL count ve Redis quarantine verisini preflight ile karsilastir.
5. App, BilgeAPI, CMS, DeerFlow, worker, beat ve Telegram yuzeylerini dogrula.
6. Post-start loglarini kritik runtime ve persistence hatalari icin tara.

## Rollback

- PostgreSQL, guncel custom-format dump'tan geri yuklenebilir.
- Redis, kopyalanan `dump.rdb` dosyasindan geri yuklenebilir.
- `E:\DockerData\integration-backups\20260711` altindaki recovery kaynaklari ve
  korunan legacy VHDX degistirilmedi.
- Compact baslamazsa veya basarisiz olursa Docker degistirilmemis VHDX ile
  yeniden baslatilir ve tam dogrulama tekrar edilir.

## Uygulama Sonucu

- Preflight ve guncel logical backups: `COMPLETED`
- Controlled Compose/Docker/WSL shutdown: `COMPLETED`
- Elevated `Optimize-VHD -Mode Full`: `COMPLETED`
- Physical reclaimed space: `30557601792` bytes (`28.459 GiB`)
- Docker ve full Compose stack restore: `COMPLETED`
- PostgreSQL/Redis persistence verification: `COMPLETED`
- Worker import repair ve regression tests: `COMPLETED`
- Traceability kaydi: `COMPLETED`
- Genel sonuc: `SUCCESS`
- Detayli rapor: `MAINTENANCE_RESULTS.md`
