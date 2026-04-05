import os
import sys
import importlib
from typing import List, Tuple

def check_file(path: str) -> bool:
    exists = os.path.exists(path)
    print(f"[{'OK' if exists else 'FAIL'}] {path}")
    return exists

def check_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        print(f"[OK] Import: {module_name}")
        return True
    except Exception as e:
        print(f"[FAIL] Import: {module_name} -> {e}")
        return False

def verify_consolidation():
    print("--- Faz 12.1 MİMARİ KONSOLİDASYON DOĞRULAMA ---")
    
    critical_files = [
        "schemas.py",
        "core/agi/cognitive/metacognitive_auditor.py",
        "core/agi/cognitive/evolution_engine.py",
        "core/agi/cognitive/dream_engine.py",
    ]
    
    shims = [
        "core/agi/cognitive/sovereign_auditor.py",
        "core/agi/cognitive/self_audit.py",
        "core/agi/cognitive/memory_pruner.py",
        "core/agi/cognitive/consolidator.py",
        "core/agi/adaptation/sovereign_evolution_45.py",
        "core/agi/adaptation/evolutionary_executor.py",
    ]
    
    print("\n[BÖLÜM 1: Dosya Varlığı]")
    all_files = critical_files + shims
    files_ok = all([check_file(f) for f in all_files])
    
    print("\n[BÖLÜM 2: Kritik Modül Importları]")
    modules = [
        "schemas",
        "core.agi.cognitive.metacognitive_auditor",
        "core.agi.cognitive.evolution_engine",
        "core.agi.cognitive.dream_engine",
    ]
    modules_ok = all([check_import(m) for m in modules])
    
    print("\n[BÖLÜM 3: Shim Doğrulaması]")
    # Shims should point to masters and have aliases
    shim_test_cases = [
        ("core.agi.cognitive.sovereign_auditor", "SovereignCortexAuditor"),
        ("core.agi.cognitive.self_audit", "SelfAuditAgent"),
        ("core.agi.cognitive.memory_pruner", "MemoryPruner"),
        ("core.agi.adaptation.sovereign_evolution_45", "SovereignEvolution45"),
    ]
    
    shims_ok = True
    for mod_name, attr in shim_test_cases:
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, attr):
                print(f"[OK] Shim {mod_name} has alias {attr}")
            else:
                print(f"[FAIL] Shim {mod_name} MISSING alias {attr}")
                shims_ok = False
        except Exception as e:
            print(f"[FAIL] Shim {mod_name} import error: {e}")
            shims_ok = False

    print("\n--- SONUÇ ---")
    if files_ok and modules_ok and shims_ok:
        print("SİSTEM BÜTÜNLÜĞÜ: KORUNUYOR (CONSOLIDATED)")
        sys.exit(0)
    else:
        print("SİSTEM BÜTÜNLÜĞÜ: KRİTİK HATALAR VAR!")
        sys.exit(1)

if __name__ == "__main__":
    verify_consolidation()
