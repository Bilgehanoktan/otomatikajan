import os
import sys

def check_dir(path: str, description: str) -> bool:
    if os.path.exists(path) and os.path.isdir(path):
        print(f"[OK] {description} bulundu: {path}")
        return True
    else:
        print(f"[FAIL] {description} EKSİK: {path}")
        return False

def check_file(path: str, description: str) -> bool:
    if os.path.exists(path) and os.path.isfile(path):
        print(f"[OK] {description} bulundu: {path}")
        return True
    else:
        print(f"[FAIL] {description} EKSİK: {path}")
        return False

def get_repo_root() -> str:
    # Assuming the script is in scripts/harness/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
