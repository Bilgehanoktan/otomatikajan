import os
import subprocess
import time

def check_root_cleanliness():
    root_files = os.listdir(".")
    dirty_files = [f for f in root_files if f.endswith(".db") or f.endswith(".sqlite") or f.endswith(".log")]
    if dirty_files:
        print(f"[FAIL] Root is NOT clean. Found: {dirty_files}")
    else:
        print("[OK] Root is clean of .db and .log files.")
    
    dirty_dirs = ["memory", "vault", "workspace", "uploads"]
    found_dirs = [d for d in dirty_dirs if os.path.isdir(d)]
    if found_dirs:
        # Check if they are empty
        for d in found_dirs:
            if os.listdir(d):
                print(f"[FAIL] Root directory '{d}' is NOT empty.")
            else:
                print(f"[WARN] Root directory '{d}' is empty but exists.")
    else:
        print("[OK] Root is clean of legacy directories.")

def check_bridge_stability():
    try:
        result = subprocess.run(["docker", "ps", "-f", "name=deerflow-bridge", "--format", "{{.Status}}"], capture_output=True, text=True)
        status = result.stdout.strip()
        if "Up" in status and "Restarting" not in status:
            print(f"[OK] Bridge is stable: {status}")
        else:
            print(f"[FAIL] Bridge is NOT stable: {status}")
            # Get last logs
            logs = subprocess.run(["docker", "logs", "--tail", "20", "deerflow-bridge"], capture_output=True, text=True)
            print("--- Last 20 lines of logs ---")
            print(logs.stdout)
            print(logs.stderr)
    except Exception as e:
        print(f"[FAIL] Error checking bridge: {e}")

def check_data_locations():
    data_path = "runtime/data"
    expected = ["cortex_local.db", "memory_vault"]
    for item in expected:
        path = os.path.join(data_path, item)
        if os.path.exists(path):
            print(f"[OK] Found {item} in {data_path}")
        else:
            print(f"[FAIL] Missing {item} in {data_path}")

if __name__ == "__main__":
    print("--- RC1.8 Verification ---")
    check_root_cleanliness()
    check_data_locations()
    print("Waiting 10s for bridge to stabilize...")
    time.sleep(10)
    check_bridge_stability()
