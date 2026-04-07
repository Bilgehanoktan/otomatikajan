#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from datetime import datetime

def run_tests():
    print("--- Beceri Katmani Dayaniklilik Kontrolu Baslatiliyor ---")
    print(f"Zaman: {datetime.now().isoformat()}")
    print("-" * 50)

    test_targets = [
        "tests/skills/",
        "tests/api/test_skills_router.py",
        "tests/core/test_skill_integration.py",
        "tests/core/test_system_indexer_skills.py",
        "tests/core/test_e2e_skill_workflows.py",
        "tests/core/test_skill_persistence.py"
    ]

    cmd = [sys.executable, "-m", "pytest"] + test_targets
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("OK: TUM TESTLER GECTI (32/32)")
            print(result.stdout.split("============================")[-1].strip())
            return True
        else:
            print("HATA: BAZI TESTLER BASARISIZ OLDU!")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"HATA: Test calistirilamadi: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
