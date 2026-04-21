import os
import subprocess
import sys
import time

def kill_process_by_port(port):
    """Portu kullanan tüm süreçleri bulur ve zorla kapatır."""
    try:
        # Netstat ile portu kullanan PID'leri bul
        result = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode('utf-8')
        pids = set()
        for line in result.strip().split('\n'):
            parts = line.split()
            if len(parts) > 4:
                pid = parts[-1]
                if pid != "0":
                    pids.add(pid)
        
        for pid in pids:
            print(f"[*] Port {port} üzerinde asılı kalan süreç kapatılıyor (PID: {pid})...")
            subprocess.run(f"taskkill /F /PID {pid} /T", shell=True, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def cleanup_system():
    print("=== SOVEREIGN AGI | INFRA SURGEON ===")
    ports = [8000, 3100, 3000]
    
    # 1. Port bazlı temizlik
    for port in ports:
        kill_process_by_port(port)
        
    # 2. Dosya Sistemi Temizliği (Kalıntılar)
    print("[*] Cache ve geçici dosyalar temizleniyor...")
    paths_to_clean = [
        "**/__pycache__",
        "apps/refine_control_plane/.next/cache"
    ]
    
    for path in paths_to_clean:
        if "**" in path:
            # Recursive pycache cleaning
            subprocess.run(f'for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"', shell=True, stderr=subprocess.DEVNULL)
        elif os.path.exists(path):
            subprocess.run(f'rd /s /q "{path}"', shell=True, stderr=subprocess.DEVNULL)

    # 3. Genel kalıntı temizliği (uvicorn ve node)
    print("[*] Süreç kalıntıları temizleniyor...")
    commands = [
        'taskkill /F /IM node.exe /T',
        'taskkill /F /IM python.exe /T /FI "COMMANDLINE eq *uvicorn*"'
    ]
    for cmd in commands:
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    # 4. Kısa bekleme (OS'un portu serbest bırakması için)
    time.sleep(1)
    print("[OK] Sistem tamamen sterilize edildi. Başlatılmaya hazır.")

if __name__ == "__main__":
    cleanup_system()
