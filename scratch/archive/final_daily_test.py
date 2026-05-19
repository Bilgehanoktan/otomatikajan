import requests
import sys

SERVICES = {
    "Mission Control (Backend)": "http://localhost:8080",
    "Launch Gatekeeper API": "http://localhost:8080/api/v1/ops/launch-gates",
    "Sovereign Cockpit (UI)": "http://localhost:3000",
    "Fleet Hub Status": "http://localhost:8080/api/v1/fleet/status",
    "Audit Ledger Data": "http://localhost:8080/api/v1/fleet/evidence"
}

def final_test():
    print("--- BUGÜNÜN FİNAL SİSTEM DOĞRULAMASI ---")
    results = []
    for name, url in SERVICES.items():
        try:
            resp = requests.get(url, timeout=5)
            status = resp.status_code
            if status == 200:
                print(f"[PASSED] {name:<30} -> {status} (OK)")
                results.append(True)
            else:
                print(f"[FAILED] {name:<30} -> {status}")
                results.append(False)
        except Exception as e:
            print(f"[ERROR ] {name:<30} -> {str(e)}")
            results.append(False)
    
    if all(results):
        print("\nSONUÇ: TÜM SİSTEMLER OPERASYONEL. EGEMEN OPERATÖRÜ İÇİN HAZIR.")
    else:
        print("\nSONUÇ: BAZI SERVİSLERDE SORUN VAR.")

if __name__ == "__main__":
    final_test()
