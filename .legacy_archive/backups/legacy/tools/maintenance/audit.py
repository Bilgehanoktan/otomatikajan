import subprocess
import os
import sys

def run_audit():
    """Tüm regresyon ve parity testlerini tek seferde koşturan denetim script'i."""
    print("======================================================================")
    print("                OTONOM AJAN SIRKETI - SISTEM DENETIMI                 ")
    print("======================================================================")
    
    test_files = [
        "tests/test_parity_llm_cost.py",
        "tests/test_regression_config_auth.py",
        "tests/test_regression_planner_orchestrator.py",
        "tests/test_regression_startup_ui_monitoring.py",
    ]
    
    passed_all = True
    for t in test_files:
        print(f"\n[RUNNING] {t} kosuluyor...")
        # pytest -q (quiet) --no-cov (hiz icin)
        res = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-cov", t], 
                             capture_output=True, text=True)
        
        if res.returncode == 0:
            print(f"[OK] PASSED: {t}")
        else:
            print(f"[FAIL] FAILED: {t}")
            print("--- HATA DETAYI ---")
            print(res.stdout + res.stderr)
            passed_all = False

    print("\n\n" + "="*70)
    if passed_all:
        print("\n\n[SUCCESS] SISTEM SAGLIKLI! Tum regresyon ve parity bariyerleri yesil.")
    else:
        print("\n\n[CRITICAL] SISTEM HATALAR ICERIYOR! Lutfen yukarıdaki detayları inceleyin.")
    print("="*70)

if __name__ == "__main__":
    run_audit()
