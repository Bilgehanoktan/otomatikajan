# Docker VHDX Compact Bakim Sonuclari

## Sonuc

- Genel bakim durumu: `SUCCESS`
- Fiziksel compact: `SUCCESS`
- Yontem: `Optimize-VHD -Mode Full`
- Yonetici baglami: `True`
- `--allow-unsafe` kullanildi: `False`
- Docker stack geri yuklendi: `True`
- Veri kaybi tespit edildi: `False`

Onceki iki UAC iptali ve ilk kabul edilen denemedeki Windows PowerShell 5.1
path-encoding hatasi guvenli sekilde durdu; bu denemelerde `Optimize-VHD`
baslamadi ve VHDX degismedi. Script path'i `$env:LOCALAPPDATA` uzerinden
cozecek sekilde duzeltildikten sonra ayni bakim penceresinde compact tamamlandi.

## VHDX

- Path: `C:\Users\BİLGEHAN\AppData\Local\Docker\wsl\disk\docker_data.vhdx`
- Compact oncesi: `62502469632` bytes (`58.210 GiB`)
- `Optimize-VHD` sonrasi: `31944867840` bytes (`29.751 GiB`)
- Geri kazanilan: `30557601792` bytes (`28.459 GiB`)
- Docker yeniden baslatildiktan sonraki canli olcum:
  `32481738752` bytes (`30.251 GiB`)
- Son C drive bos alani: `36848345088` bytes (`34.318 GiB`)

Docker Desktop'in yeniden baslamasindan sonraki yaklasik `0.500 GiB` buyume,
aktif runtime yazimlarindan kaynaklanan normal degisimdir. Elevated script sonucu
`compact-result.json` icinde saklanmistir.

## Guncel Yedekler

- PostgreSQL dump: `ai_company_pre_vhdx_compact_retry_20260720.dump`
- PostgreSQL dump bytes: `2850103`
- PostgreSQL SHA256:
  `33EE968523E2DD81A6F67B886469C45F865E21197517DE7C46F4A725CEEA50A9`
- `pg_restore -l`: basarili, son TOC entry `5992`
- Redis RDB: `redis_pre_vhdx_compact_retry_20260720.rdb`
- Redis RDB bytes: `538657`
- Redis SHA256:
  `4D16115C6992B4B917BD92EE6407DA98880019F269D3942761284B02F0A9C9D5`
- `redis-check-rdb`: checksum OK, `2102` keys, `3` already expired
- Elevated script SHA256:
  `E6E47AB16DE7264920E7BD16E323E5AF1CD56A04CFF2DB6278625DE8D0781B1A`

## Kalicilik Karsilastirmasi

| Veri | Compact oncesi | Son kontrol | Sonuc |
| --- | ---: | ---: | --- |
| `projects` | 54 | 54 | korundu |
| `subtasks` | 504 | 504 | korundu |
| `bilgeapi_api_keys` | 3 | 3 | korundu |
| `bilgeapi_audit_events` | 1528 | 1528 | korundu |
| `repair_ui_pr_reviews` | 55 | 55 | korundu |
| `bilgeapi_review_ledger_entries` | 3970 | 3987 | startup audit kayitlariyla artti |
| `memories` | 2 | 3 | bu basarili EpisodeRecord ile artti |
| Celery quarantine list | 3 | 3 | korundu |

Redis `PONG` dondurdu. `DBSIZE` TTL ve aktif servis yazimlari nedeniyle dinamik
oldugundan veri-kaybi kriteri olarak kullanilmadi; kalici quarantine listesi ve
PostgreSQL is verileri korundu.

## Restart Sirasinda Bulunan ve Duzeltilen Hata

Full restart, `worker`, `deerflow-worker` ve `beat` servislerinde root repository
modullerinin yalnizca `/app` `PYTHONPATH` ile `bilgeapi.*` alias'ina bagli oldugunu
ortaya cikardi.

Duzeltmeler:

- `libs/db/repositories/repository.py` icindeki mevcut `libs.db.models`
  namespace kullaniminin root-only worker baglaminda calistigi dogrulandi; bu
  dosyadaki compact bakimindan bagimsiz mevcut worktree farklari geri alinmadi.
- `libs/db/repositories/repair_repository.py`, root-only worker importunun
  optional repair servisleri bulunmadiginda cokmemesi icin `ImportError`
  guard'lariyla guclendirildi.
- `tests/unit/bilgeapi/test_model_import_isolation.py`, root-only `PYTHONPATH`
  import regresyonunu kapsiyor.
- Daha once bulunan startup event-loop ve duplicate model alias duzeltmeleri
  `apps/bilgeapi/startup.py` ve `libs/db/models/__init__.py` icinde korundu.

## Dogrulama

- Son odakli pytest paketi: `20/20 passed`
- Import-focused Ruff: basarili
- Compose servisleri: `10/10 running`
- Celery inspect: `2` node online, ikisi de `pong`
- Main app: healthy, `FULL_AUTONOMOUS`, DB/Redis/repair/governance healthy
- BilgeAPI: healthy
- CMS `/login`: `200`
- DeerFlow: healthy
- Migration: `5cf84776dfef (head)`
- Telegram configuration: valid, recipient count `1`; bu compact bakiminda canli
  Telegram mesaji gonderilmedi.
- Basarili worker restart'inden sonraki log taramasi:
  `ModuleNotFoundError`, `MissingGreenlet`, duplicate metadata, `ERROR`,
  `CRITICAL`, `Traceback`, DB interruption, Redis `MISCONF` ve Telegram conflict
  bulunmadi.
- Basarili traceability EpisodeRecord:
  `97538392-1872-4b1b-858d-73f5b39f9c97`, `7` ActionRecord.
- Onceki engellenen deneme EpisodeRecord:
  `6b5cedc7-b7b9-46c6-ae49-9d0370fd7aad`.

## Sonraki Islem

Yeni PostgreSQL ve Redis yedekleri en az bir gozlem penceresi boyunca
korunmalidir. Bunlarin silinmesi veya eski recovery anchor'larinin temizlenmesi
bu bakimin parcasi degildir ve ayri, acik bir onay gerektirir.
