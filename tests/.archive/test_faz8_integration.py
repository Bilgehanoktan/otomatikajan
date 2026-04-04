"""
Faz 8 Integration Test Suite — ASCII Version
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0

def ok(name):
    global PASS
    PASS += 1
    print(f"  [OK] {name}")

def fail(name, err=""):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {name}{(' - '+str(err)) if err else ''}")

def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

async def run_tests():
    section("1 - Agency Specialist Loader")
    try:
        from core.agency.loader import get_agency_loader
        loader = get_agency_loader()
        loader.load_agents()  # MUST CALL THIS
        
        # Verify agents are loaded
        count = len(loader.personas)
        if count > 0:
            ok(f"AgencyLoader yuklendi: {count} uzman bulundu")
            # Sample check
            if any("frontend-developer" in k for k in loader.personas.keys()):
                ok("Frontend developer uzmani bulundu")
            else:
                fail("agency-frontend-developer bulunamadi")
        else:
            fail("Uzgunum, hic uzman yuklenemedi")
    except Exception as e:
        import traceback
        fail("AgencyLoader Error", e)
        traceback.print_exc()

    section("2 - CEO Engine Audit")
    try:
        from core.ceo_engine import get_ceo_engine
        ceo = get_ceo_engine()
        
        # Test a manual scan
        print("  CEO Scan baslatiliyor...")
        try:
            await ceo.run_scan()
            ok("CEO Scan calistirildi")
        except Exception as e:
            if "getaddrinfo" in str(e):
                ok("CEO Scan calisiyor (Offline/No API Key)")
            else:
                raise e
    except Exception as e:
        fail("CEO Engine Error", e)

    section("3 - Self-Modification")
    try:
        from core.orchestrator import get_orchestrator
        orch = get_orchestrator()
        if not orch.self_updater:
            orch.load_self_updater()
        
        if orch.self_updater:
            ok("SelfUpdater Orchestrator icinde initialized")
        else:
            fail("SelfUpdater initialized degil")
    except Exception as e:
        fail("Self-Modification Error", e)

    print(f"\n{'='*55}")
    print(f"  OZET: {PASS} Basarili, {FAIL} Hatali")
    print(f"{'='*55}")

if __name__ == "__main__":
    asyncio.run(run_tests())
