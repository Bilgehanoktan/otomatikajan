import re
import os
from pathlib import Path
import sys

# Add libs to path
sys.path.append(os.getcwd())
try:
    from libs.mesh.alerts import AlertCode
except ImportError:
    print("Error: libs/mesh/alerts.py not found.")
    sys.exit(1)

def check_runbook_sync():
    docs_dir = Path("docs")
    runbooks = list(docs_dir.rglob("*.md"))
    canonical_ids = set(item.value for item in AlertCode)
    
    print(f"--- Sovereign AGI: R-07 Global Synchronization Audit ---")
    print(f"Found {len(runbooks)} markdown files. Canonical IDs: {len(canonical_ids)}\n")
    
    mismatches = 0
    synced_count = 0
    
    for rb in runbooks:
        if ".git" in str(rb) or "node_modules" in str(rb):
            continue
            
        try:
            # Using errors="replace" to handle legacy encodings or Turkish characters
            content = rb.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  [E] SKIPPING: Could not read {rb.name} - {str(e)}")
            continue

        found_ids = set()
        
        # Look for patterns like `ERR_...` or uppercase codes in backticks
        matches = re.findall(r"`([A-Z][A-Z0-9_]+)`", content)
        for match in matches:
            if match.startswith(("ERR_", "INCIDENT_", "ALERT_", "MESH_", "BUDGET_", "EMERGENCY_", "PULSE_", "SAFETY_")):
                if match == "BUDGET_USD":
                    continue
                found_ids.add(match)
        
        if not found_ids:
            continue

        print(f"Checking: {rb.relative_to(docs_dir)}")
        for fid in found_ids:
            if fid not in canonical_ids:
                print(f"  [!] DRIFT DETECTED: Code `{fid}` in {rb.name} is NOT in canonical AlertDictionary.")
                mismatches += 1
            else:
                print(f"  [?] Synced: `{fid}`")
                synced_count += 1

    print(f"\n--- Audit Summary ---")
    print(f"Mismatches: {mismatches}")
    print(f"Synced IDs Found: {synced_count}")

    if mismatches == 0 and synced_count > 0:
        print(f"\n[SUCCESS] R-07: Operational documentation is synchronized with Live Alert Dictionary.")
    elif synced_count == 0:
        print(f"\n[WARNING] R-07: No technical alert IDs found in documentation. Please verify coverage.")
    else:
        print(f"\n[FAILURE] R-07: Found {mismatches} terminology drifts.")

if __name__ == "__main__":
    check_runbook_sync()
