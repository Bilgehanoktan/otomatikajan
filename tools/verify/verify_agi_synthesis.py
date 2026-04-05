import asyncio
import os
import sys

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_synthesis():
    print("--- AGI 12.4 Verification ---")
    
    try:
        from core.agi.operational.tool_weaver import tool_weaver, tool_registry
        from core.agi.world.repo_graph import repo_world_model
        from core.agi.operational.executor import OperationalExecutor
        
        print("[OK] All AGI Synthesis components imported successfully.")
        
        # Test Tool Registry
        print(f"[OK] Tool Registry initialized. Records: {len(tool_registry.list_tools())}")
        
        # Test Repo Graph Discovery
        # Manuel olarak bir kayıt ekleyip deniyoruz
        tool_registry.register("test_fibo", "tools/autonomous/test_fibo.py", "Calculates fibonacci", {"n": "int"})
        repo_world_model.scan()
        summary = repo_world_model.get_summary()
        found = any("capability:test_fibo" in k for k in repo_world_model.nodes.keys())
        print(f"[OK] Repo Graph discovery: {found}")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_synthesis())
