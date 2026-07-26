# Ikinci Compact Preflight Manifest

- Timestamp: `2026-07-20 22:17-22:20 Europe/Istanbul`
- Operator context administrator: `False`
- Active VHDX:
  `C:\Users\BİLGEHAN\AppData\Local\Docker\wsl\disk\docker_data.vhdx`
- VHDX pre-compact bytes: `32481738752`
- VHDX pre-compact size: `30.251 GiB`
- Running Compose services: `10`

## PostgreSQL Baseline

- `projects=54`
- `subtasks=504`
- `bilgeapi_api_keys=3`
- `bilgeapi_audit_events=1528`
- `repair_ui_pr_reviews=55`
- `bilgeapi_review_ledger_entries=3987`
- `memories=3`
- Dump: `ai_company_pre_second_compact_20260720-221738.dump`
- Dump bytes: `2858751`
- Dump SHA256:
  `83C75CD4ECFD7412A8C035744FE25217B79D530E8C246982E516C70B6FAE47D9`
- `pg_restore -l`: basarili, final TOC entry `5992`

## Redis Baseline

- `PING=PONG`
- `DBSIZE=2007`
- Celery quarantine length: `3`
- RDB: `redis_pre_second_compact_20260720-221738.rdb`
- RDB bytes: `507099`
- RDB SHA256:
  `651638126636363FC867F3C4ADBB6B9C769E47B612E08E8B33049886E13BA91C`
- `redis-check-rdb`: checksum OK, `2006` keys, `0` already expired

## Elevated Script

- Script: `compact-vhdx.ps1`
- SHA256:
  `6D6720DD51D267923820CF725D968E5BD2B3A134E65B6A085A0C587E8014BC73`
- Path resolution: `$env:LOCALAPPDATA`
- Mode: `Full`
- Unsafe compact option: prohibited
