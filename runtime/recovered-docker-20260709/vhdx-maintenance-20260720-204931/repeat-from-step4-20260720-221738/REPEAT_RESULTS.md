# Docker VHDX Compact Tekrar Sonuclari

## Sonuc

- Kapsam: Onceki planin 4. adimindan itibaren tekrar
- Genel durum: `SUCCESS`
- Elevated compact: `SUCCESS`
- Mode: `Optimize-VHD -Mode Full`
- Administrator context: `True`
- Unsafe compact secenegi kullanildi: `False`
- Veri kaybi tespit edildi: `False`

## VHDX Sonucu

- Tekrar preflight olcumu: `32481738752` bytes (`30.251 GiB`)
- Elevated script compact-oncesi olcumu: `32472301568` bytes (`30.249 GiB`)
- Elevated script compact-sonrasi olcumu: `32472301568` bytes (`30.249 GiB`)
- Ek reclaimed alan: `0` bytes
- Full stack ve testler sonrasi canli olcum:
  `33109835776` bytes (`30.836 GiB`)
- Son C drive bos alani: `36179279872` bytes (`33.695 GiB`)

Ikinci `Optimize-VHD -Mode Full` exit code `0` ile tamamlandi. Ek alan
kazanilmamasi, ilk compact sonrasi VHDX'in zaten optimize durumda oldugunu ve
ikinci calismanin idempotent no-op oldugunu gosterir. Restart sonrasi buyume
aktif Docker runtime, log ve test yazimlaridir.

## Ikinci Calisma Yedekleri

- PostgreSQL dump: `ai_company_pre_second_compact_20260720-221738.dump`
- Bytes: `2858751`
- SHA256:
  `83C75CD4ECFD7412A8C035744FE25217B79D530E8C246982E516C70B6FAE47D9`
- `pg_restore -l`: basarili, final TOC entry `5992`
- Redis RDB: `redis_pre_second_compact_20260720-221738.rdb`
- Bytes: `507099`
- SHA256:
  `651638126636363FC867F3C4ADBB6B9C769E47B612E08E8B33049886E13BA91C`
- `redis-check-rdb`: checksum OK, `2006` keys, `0` already expired
- Elevated script SHA256:
  `6D6720DD51D267923820CF725D968E5BD2B3A134E65B6A085A0C587E8014BC73`

## Kalicilik Karsilastirmasi

| Veri | Tekrar oncesi | Tekrar sonrasi | Sonuc |
| --- | ---: | ---: | --- |
| `projects` | 54 | 54 | korundu |
| `subtasks` | 504 | 504 | korundu |
| `bilgeapi_api_keys` | 3 | 3 | korundu |
| `bilgeapi_audit_events` | 1528 | 1528 | korundu |
| `repair_ui_pr_reviews` | 55 | 55 | korundu |
| `bilgeapi_review_ledger_entries` | 3987 | 4004 | startup audit kayitlariyla artti |
| `memories` | 3 | 4 | bu EpisodeRecord ile artti |
| Celery quarantine list | 3 | 3 | korundu |

Redis `PONG` dondurdu. `DBSIZE` aktif TTL verisi nedeniyle `2007` ile `1972`
arasinda degisti; kalici quarantine listesi ve PostgreSQL is verileri korundu.

## Runtime Dogrulamasi

- Compose servisleri: `10/10 running`
- Health wait: basarili
- HTTP: app, BilgeAPI, CMS ve DeerFlow `4/4 status 200`
- Celery: `2/2` node `pong`
- Migration: `5cf84776dfef`
- Telegram: enabled, token/webhook secret configured, allowed recipient `1`,
  admin recipient `1`; bu tekrar calismasinda canli mesaj gonderilmedi
- Post-restart kritik log eslesmesi: `0`
- Host Python regresyon paketi: `20/20 passed`

Container icindeki pytest denemesi urun testi baslamadan ortam seviyesinde durdu:
mounted SQLite test DB read-only ve image icinde `pytest-cov` yoktu. Ayni testler
host Python 3.14 ile basarili calistirildi; bu durum urun test failure degildir.

## Izlenebilirlik

- EpisodeRecord: `529215a3-9cae-49dc-9c8e-4e92328917e9`
- Memory record: `4b5131da-55fa-409b-85bb-f2eeb190b8e4`
- ActionRecord count: `6`
- Verification result: `true`
- Data loss detected: `false`

Ikinci calismanin logical yedekleri bir gozlem penceresi boyunca korunmalidir.
