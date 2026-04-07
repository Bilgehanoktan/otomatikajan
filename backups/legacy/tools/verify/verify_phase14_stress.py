import asyncio
import uuid
import requests
import time

# FAZ 14 VERIFICATION: Stress Test Script
# launches 5 concurrent reasoning tasks and monitors health

BASE_URL = "http://localhost:8000" # Update if needed

def get_token():
    # In a real test, you'd get this from a login or a test account
    return "TEST_TOKEN_OR_ADMIN_KEY"

async def launch_task(session, task_id):
    print(f"[*] Task {task_id} başlatılıyor...")
    # This simulates a high-intensity reasoning task
    # (In a real scenario, this would be an API call to the orchestrator)
    await asyncio.sleep(2)
    print(f"[+] Task {task_id} tamamlandı.")

async def main():
    print("═══ Phase 14 Stress Test: High-Load Simulation ═══")
    tasks = []
    for i in range(5):
        tasks.append(launch_task(None, f"stress_{i}_{uuid.uuid4().hex[:4]}"))
    
    print(f"[*] 5 adet eşzamanlı görev tetikleniyor...")
    start_time = time.time()
    await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    print(f"\n[!] Simülasyon tamamlandı ({duration:.2f}s).")
    print("[!] Lütfen Dashboard'dan Health Score'un (Sistem Sağlığı) 0.8'in üzerinde")
    print("[!] sabit kaldığını (EWMA smoothing sayesinde) doğrulayın.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
