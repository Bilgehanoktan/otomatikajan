import asyncio
import os
from core.safety_gate import safety_gate

async def test_protection():
    file_to_test = "main.py"
    print(f"[*] Testing protection for: {file_to_test}")
    try:
        safety_gate.check_access(file_to_test)
        print("[!] PROTECTION FAILED: main.py should be frozen!")
    except PermissionError as e:
        print(f"[OK] PROTECTION ACTIVE: {e}")

    # Test un-tracked and non-critical file
    print("[*] Testing non-critical file: temp_test.txt")
    safety_gate.check_access("temp_test.txt")
    print("[OK] Access allowed for temp_test.txt")

if __name__ == "__main__":
    asyncio.run(test_protection())
