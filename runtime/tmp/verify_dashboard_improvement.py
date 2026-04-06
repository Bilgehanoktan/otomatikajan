
import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from core.self_updater import SelfUpdater
from packages.llm_gateway.model_orchestrator import ModelOrchestrator

async def verify_dashboard_support():
    print("--- Dashboard Support Verification ---")
    
    model_orch = ModelOrchestrator()
    updater = SelfUpdater(model_orch=model_orch, project_root=str(project_root))
    
    target_file = "dashboard/index.html"
    
    print(f"Testing path resolution for: {target_file}")
    try:
        resolved_path = updater._resolve_target_path(target_file)
        print(f"[OK] Resolved path: {resolved_path}")
    except Exception as e:
        print(f"[ERROR] Resolution failed: {e}")
        return

    print("\nTesting HTML validation...")
    valid_html = "<html><body><h1>Test</h1></body></html>"
    invalid_html = "This is not html"
    
    try:
        updater._validate_code(valid_html, target_file)
        print("[OK] Valid HTML passed.")
    except Exception as e:
        print(f"[ERROR] Valid HTML failed: {e}")

    try:
        updater._validate_code(invalid_html, target_file)
        print("[ERROR] Invalid HTML passed (Expected failure).")
    except Exception as e:
        print(f"[OK] Invalid HTML failed as expected: {e}")

    print("\nTesting ShadowRunner syntax check for HTML...")
    from core.shadow_runner import ShadowRunner
    runner = ShadowRunner(project_root=str(project_root))
    
    # Mocking a Path object with .suffix == ".html"
    class MockPath:
        def __init__(self, suffix):
            self.suffix = suffix
    
    try:
        runner._validate_syntax(MockPath(".html"), "Any content")
        print("[OK] ShadowRunner skipped Python syntax check for HTML.")
    except Exception as e:
        print(f"[ERROR] ShadowRunner failed for HTML: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_dashboard_support())
