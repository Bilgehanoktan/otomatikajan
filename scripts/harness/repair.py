import os
import sys
import argparse
from harness_utils import get_repo_root

def run_repair(dry_run=False):
    root = get_repo_root()
    print(f"--- Codex Harness Repair {'(DRY RUN)' if dry_run else ''} ---")
    
    # 1. Eksik klasörleri oluştur
    for d in [".codex", ".agents/skills", "rules", "scripts/harness"]:
        path = os.path.join(root, d)
        if not os.path.exists(path):
            if dry_run:
                print(f"[DRY-RUN] Klasör oluşturulacaktı: {d}")
            else:
                print(f"[FIX] Klasör oluşturuluyor: {d}")
                os.makedirs(path)
            
    # 2. Eksik config.toml'u oluştur (varsayılan)
    config_path = os.path.join(root, ".codex/config.toml")
    if not os.path.exists(config_path):
        if dry_run:
            print(f"[DRY-RUN] Varsayılan config.toml oluşturulacaktı.")
        else:
            print(f"[FIX] Varsayılan config.toml oluşturuluyor.")
            with open(config_path, "w") as f:
                f.write("# Default Codex Config\n[project]\nname = 'Sovereign AGI'\n")
            
    # 3. Disk Alanı Temizliği (Faz 12.1 Reclaim)
    runtime_dir = os.path.join(root, "runtime")
    if os.path.exists(runtime_dir):
        import time
        now = time.time()
        deleted_count = 0
        
        print(f"[RECLAIM] Eski runtime klasörleri taranıyor...")
        for d in os.listdir(runtime_dir):
            path = os.path.join(runtime_dir, d)
            if os.path.isdir(path) and d.startswith("run_"):
                # 24 saatten eski ise sil
                if now - os.path.getmtime(path) > 86400:
                    try:
                        if dry_run:
                            print(f"  [DRY-RUN] Silinecek klasör: {d}")
                            deleted_count += 1
                        else:
                            import shutil
                            shutil.rmtree(path)
                            deleted_count += 1
                    except Exception as e:
                        print(f"  [ERROR] {d} silinemedi: {e}")
        
        if deleted_count > 0:
            msg = "silinecek" if dry_run else "temizlendi"
            print(f"[OK] {deleted_count} eski runtime klasörü {msg}.")
            
    print(f"\n--- Onarım bitti. Lütfen 'doctor' komutu ile tekrar kontrol edin. ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Değişiklik yapmadan simüle et.")
    args = parser.parse_args()
    run_repair(dry_run=args.dry_run)
