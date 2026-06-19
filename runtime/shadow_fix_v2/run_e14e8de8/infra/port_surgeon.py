"""
Sovereign AGI | Infrastructure Port Surgeon
Temizlik araci: Belirtilen portlarda asili kalan surecleri tespit edip kapatir.
"""
import os
import shutil
import subprocess
import time


# Temizlenecek portlar
TARGET_PORTS = [8000, 3100, 3000]

# Bu scriptin kendi PID'si - kendimizi oldurmeyelim
MY_PID = str(os.getpid())


def kill_process_by_port(port: int) -> bool:
    """Portu kullanan tum surecleri bulur ve zorla kapatir."""
    try:
        result = subprocess.check_output(
            ["netstat", "-ano"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="replace")

        pids = set()
        for line in result.strip().split("\n"):
            parts = line.split()
            if len(parts) > 4 and parts[1].endswith(f":{port}"):
                pid = parts[-1].strip()
                # PID 0 ve kendi PID'imizi atlayalim
                if pid != "0" and pid != MY_PID and pid.isdigit():
                    pids.add(pid)

        if not pids:
            print(f"    Port {port}: Temiz (asili surec yok)")
            return False

        for pid in pids:
            print(f"    Port {port}: Asili surec kapatiliyor (PID: {pid})...")
            subprocess.run(
                ["taskkill", "/F", "/PID", pid],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return True

    except subprocess.CalledProcessError:
        print(f"    Port {port}: Temiz (asili surec yok)")
        return False


def cleanup_cache():
    """Gecici cache dosyalarini temizler."""
    print("[*] Cache temizligi yapiliyor...")
    cache_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "apps", "refine_control_plane", ".next", "cache"
    )
    if os.path.exists(cache_path):
        try:
            shutil.rmtree(cache_path)
            print("    .next/cache temizlendi.")
        except Exception:
            print("    .next/cache temizlenemedi (atlaniyor).")
    else:
        print("    Cache dizini temiz.")


def main():
    print("=== SOVEREIGN AGI | INFRA SURGEON ===")
    print(f"    Kendi PID: {MY_PID} (korunuyor)")
    print()

    # 1. Port bazli temizlik
    print("[*] Port bazli surec temizligi baslatiliyor...")
    cleaned = False
    for port in TARGET_PORTS:
        if kill_process_by_port(port):
            cleaned = True

    # 2. Cache temizligi
    cleanup_cache()

    # 3. Portlarin serbest kalmasi icin kisa bekleme
    if cleaned:
        print("[*] Portlarin serbest kalmasi bekleniyor...")
        time.sleep(1)

    print()
    print("[OK] Sistem sterilize edildi. Baslatilmaya hazir.")


if __name__ == "__main__":
    main()
