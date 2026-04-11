import sys
import time
import threading

def probe(msg):
    print(f"[PROBE] {time.strftime('%H:%M:%S')} - {msg}", flush=True)

def timeout_check():
    time.sleep(10)
    print("\n[TIMEOUT] Import hang detected! The system is still deadlocked.", flush=True)
    # We don't exit to see the verbose output if any
    
threading.Thread(target=timeout_check, daemon=True).start()

probe("Starting import of SovereignCortex...")
try:
    from packages.orchestration.application.sovereign_cortex import SovereignCortex
    probe("SUCCESS: SovereignCortex imported without hang.")
except Exception as e:
    probe(f"ERROR: Import failed with: {str(e)}")
