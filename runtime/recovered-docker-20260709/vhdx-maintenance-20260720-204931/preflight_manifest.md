# VHDX Compact Preflight Manifest

- Timestamp: `2026-07-20 20:49-20:50 Europe/Istanbul`
- Operator context administrator: `False`
- Docker Desktop: running, engine `29.6.1`, context `desktop-linux`
- Active VHDX:
  `C:\Users\BİLGEHAN\AppData\Local\Docker\wsl\disk\docker_data.vhdx`
- VHDX pre-compact bytes: `62502469632`
- VHDX pre-compact size: `58.210 GB`
- C drive preflight free: `3.984 GB`
- E drive preflight free: `28.034 GB`

## PostgreSQL Baseline

- `projects=54`
- `subtasks=504`
- `bilgeapi_api_keys=3`
- `bilgeapi_audit_events=1528`
- `repair_ui_pr_reviews=55`
- `bilgeapi_review_ledger_entries=3885`
- `memories=1`
- Dump: `ai_company_pre_vhdx_compact_20260720.dump`
- Dump bytes: `2837368`
- Dump SHA256:
  `4A576CC43085EC2C00351F894D7197024E0ECDDCF77CBD5093A2C07974F09083`
- `pg_restore -l`: passed, final TOC entry `5992`

## Redis Baseline

- `PING=PONG`
- Preflight `DBSIZE=1913`; validated RDB contained `1919` keys because active
  services continued writing between the two observations.
- Celery quarantine length: `3`
- RDB: `redis_pre_vhdx_compact_20260720.rdb`
- RDB bytes: `495041`
- RDB SHA256:
  `15D9CD57DBB21C3E450D866488F0EAB3EA6C928C8B5B6508BFC200223E6373D1`
- `redis-check-rdb`: checksum OK, 1919 keys, 0 already expired.

## Safety Constraints

- `--allow-unsafe` is prohibited and will not be invoked.
- No Docker volume prune, reset, VHDX move, sparse conversion, or deletion is
  authorized by this maintenance step.
- Elevated execution is limited to exact-path `Optimize-VHD -Mode Full` after
  Docker Desktop and WSL are stopped.

## Basarili Retry Snapshot

- Retry timestamp: `2026-07-20 21:55-21:56 Europe/Istanbul`
- Active path, script icinde `$env:LOCALAPPDATA` ile cozuldu:
  `C:\Users\BİLGEHAN\AppData\Local\Docker\wsl\disk\docker_data.vhdx`
- Retry PostgreSQL baseline:
  `projects=54`, `subtasks=504`, `bilgeapi_api_keys=3`,
  `bilgeapi_audit_events=1528`, `repair_ui_pr_reviews=55`,
  `bilgeapi_review_ledger_entries=3970`, `memories=2`
- Retry dump: `ai_company_pre_vhdx_compact_retry_20260720.dump`
- Retry dump SHA256:
  `33EE968523E2DD81A6F67B886469C45F865E21197517DE7C46F4A725CEEA50A9`
- Retry Redis RDB: `redis_pre_vhdx_compact_retry_20260720.rdb`
- Retry Redis SHA256:
  `4D16115C6992B4B917BD92EE6407DA98880019F269D3942761284B02F0A9C9D5`
- Retry Redis baseline: `PING=PONG`, `DBSIZE=2110`, quarantine length `3`
- VHDX before: `62502469632` bytes (`58.210 GiB`)
- VHDX immediately after: `31944867840` bytes (`29.751 GiB`)
- Reclaimed: `30557601792` bytes (`28.459 GiB`)
- Result: `SUCCESS`
- `--allow-unsafe` used: `False`
