
import sys
import os
sys.path.append(os.getcwd())

from services.governance.standby_manager import StandbyManager

def activate():
    print("Initiating System Activation Trigger...")
    # The exact phrase required by the gatekeeper
    trigger_phrase = "Hazır, PRMR-01 Faz 1’i yeniden başlat."
    
    success = StandbyManager.check_trigger(trigger_phrase)
    
    if success:
        print("SUCCESS: System Activation Authorized. Standby mode exited.")
        status = StandbyManager.get_status_report()
        print(f"Current Status: {status['mode']}")
    else:
        print("FAILED: Activation trigger rejected.")

if __name__ == "__main__":
    activate()
