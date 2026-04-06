import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def run_command(command):
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            shell=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_lint():
    print("[*] Running Linter (Ruff) check...")
    # Check if ruff exists
    code, _, _ = run_command("ruff --version")
    if code != 0:
        print("[!] WARNING: 'ruff' not found on host. Skipping linting (Will be enforced in Docker).")
        return True
    
    code, out, err = run_command("ruff check . --select E,F,W --exclude .venv,venv,node_modules,everything-claude-code-main")
    if code != 0:
        print("[!] LINT ERRORS DETECTED:")
        print(out)
        print(err)
        return False
    print("[OK] Linting passed.")
    return True

def smoke_import_test():
    print("[*] Running Import Smoke Test...")
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root))
    
    critical_modules = [
        "apps.api.main",
        "apps.api.lifespan",
        "apps.worker.tasks.celery_app",
        "packages.orchestration.agi.cognitive.sovereign_cortex",
        "packages.persistence.session"
    ]
    
    success = True
    for module_name in critical_modules:
        try:
            print(f"    [-] Testing import: {module_name}...", end=" ")
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                print("FAILED (Not found)")
                success = False
                continue
            
            # Bu adım modülü gerçekten yükler, bu yüzden NameError vb. yakalar.
            importlib.import_module(module_name)
            print("OK")
        except Exception as e:
            print(f"FAILED (Error: {e})")
            success = False
            
    return success

if __name__ == "__main__":
    print("====================================================")
    print("   Sovereign Quality Guard: Integrity Check")
    print("====================================================")
    
    lint_ok = check_lint()
    import_ok = smoke_import_test()
    
    print("----------------------------------------------------")
    if lint_ok and import_ok:
        print("[SUCCESS] System Integrity Check PASSED.")
        sys.exit(0)
    else:
        print("[FAILURE] System Integrity Check FAILED.")
        print("[!] Please fix the errors above before launching.")
        sys.exit(1)
