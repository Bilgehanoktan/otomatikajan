# Protected Cleanup Plan

Bu plan, kullanilan veriyi silmeden worktree kirliligini azaltmak icin uygulanir.

## Korumali Kurallar

- Dogrudan silme yapma.
- Once envanter cikar, sonra siniflandir, sonra gerekirse karantina kullan.
- `.env`, `.env.*`, `*.db`, `*.db-shm`, `*.db-wal`, `.deer-flow/`, `runtime/data/`, loglar ve kanit/evidence klasorleri veri olarak kabul edilir.
- `repair_outputs/` ve `artifacts/` altindaki dosyalar once kanit/veri kabul edilir; sadece operator onayi ve yedek/karantina sonrasinda temizlenir.
- Kaynak entegrasyon dosyalari generated kabul edilmez: `services/database/recovery/`, `services/telegram/`, `services/ui_repair/watchdog/`, `agents/meeting_room.py`, `agents/self_governor.py`, `tests/phases/`.

## Siniflar

- `PROTECT_DATA`: `.env`, DB/WAL/SHM, runtime data, logs, evidence, checkpoints.
- `SAFE_GENERATED`: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.next/`, tool cache ve rebuild edilebilir temp dosyalari.
- `REVIEW_ARTIFACT`: `repair_outputs/`, `artifacts/`, live smoke outputs, generated reports.
- `SOURCE_OR_INTEGRATION`: Kod, test, docs, config ve yeni entegrasyon dosyalari.

## Uygulama Sirasi

1. `scripts/ops/protected_cleanup_inventory.ps1` ile manifest uret.
2. `PROTECT_DATA` ve `REVIEW_ARTIFACT` listelerini manuel kontrol et.
3. `SAFE_GENERATED` icin once karantina planla; dogrudan `Remove-Item` kullanma.
4. Karantina sonrasi testleri calistir:
   - `py -3.13 -m pytest tests\project_factory -q`
   - `py -3.13 -m pytest tests\self_repair_audit -q`
   - `cmd /c npx tsc --noEmit`
   - `py -3.13 check_system_health.py`
5. Testler yesil kalirsa karantina klasoru icin ayri operator onayi al.

## Yasaklar

- `.env` veya DB dosyalarini temizleme hedefi yapma.
- `git clean -fdx` kullanma.
- `git reset --hard` kullanma.
- Evidence klasorlerini dogrudan silme.
- Genel `git add .` kullanma.
