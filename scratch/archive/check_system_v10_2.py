import requests
import json
import os

SERVICES = {
    "Mission Control API": "http://localhost:8000",
    "API Docs": "http://localhost:8000/docs",
    "Sovereign Cockpit UI": "http://localhost:3100",
}

def check_infra_audit():
    audit_path = "docs/audits/infra_readiness_audit_prmr_01.md"
    if os.path.exists(audit_path):
        with open(audit_path, "r", errors="ignore") as f:
            content = f.read()
            if "Ready state armed" in content:
                print("[PASSED] Audit Raporu: Ready state armed (Tespit Edildi)")
                return True
    print("[FAILED] Audit Raporu güncel değil veya 'Armed' ibaresi eksik.")
    return False

def check_standby_state():
    state_path = "runtime/data/standby_control.json"
    if os.path.exists(state_path):
        with open(state_path, "r", errors="ignore") as f:
            data = json.load(f)
            if data.get("reactivated") == True:
                print(f"[PASSED] Standby State: Reactivated (Armed) - Transition Pending")
                return True
    print("[FAILED] Standby state kilitli veya dosya bulunamadı.")
    return False

def run_tests():
    print("=== SOVEREIGN AGI | SYSTEM V10.2 TEST SERİSİ ===")
    all_ok = True
    
    # 1. Servis Kontrolleri
    for name, url in SERVICES.items():
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code < 400:
                print(f"[PASSED] {name:<20} -> {resp.status_code}")
            else:
                print(f"[FAILED] {name:<20} -> {resp.status_code}")
                all_ok = False
        except Exception as e:
            print(f"[ERROR ] {name:<20} -> Erişilemiyor")
            all_ok = False
            
    # 2. Mantıksal Durum Kontrolleri
    if not check_infra_audit(): all_ok = False
    if not check_standby_state(): all_ok = False
    
    print("\n" + "="*45)
    if all_ok:
        print("SONUÇ: SİSTEM STABİL. DEGRADED MODE AKTİF.")
    else:
        print("SONUÇ: EKSİK BİLEŞENLER VAR. (BEKLENEN DURUM)")

if __name__ == "__main__":
    run_tests()
