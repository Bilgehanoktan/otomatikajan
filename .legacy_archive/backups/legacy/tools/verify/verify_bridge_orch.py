import sys
import os

project_root = r"e:\ai_company_faz12.1"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("--- [CHECK] Bridge & Orkestrasyon Dogrulama ---")

# 1. Orchestrator init
try:
    from packages.orchestration.orchestrator import Orchestrator
    o = Orchestrator()
    print(f"[OK] Orchestrator baslatildi. self_updater={o.self_updater}, agents={o.agent_count()}")
except Exception as e:
    print(f"[ERR] Orchestrator: {e}")

# 2. Bridge app import
try:
    from deerflow_bridge.app import app
    print(f"[OK] Bridge app import basarili. Title: {app.title}")
except Exception as e:
    print(f"[ERR] Bridge app: {e}")

# 3. _normalize_status
try:
    from tasks.deerflow_tasks import _normalize_status
    from packages.persistence.models import ProjectStatus
    # String test
    assert _normalize_status("running") == "running"
    # Enum test  
    completed_val = _normalize_status(ProjectStatus.COMPLETED)
    assert completed_val != ""
    # None test
    assert _normalize_status(None) == ""
    print(f"[OK] _normalize_status: String={_normalize_status('running')}, Enum={completed_val}, None={_normalize_status(None)}")
except Exception as e:
    print(f"[ERR] _normalize_status: {e}")

# 4. DeerFlowBridgeClient import
try:
    from integrations.deerflow_bridge import DeerFlowBridgeClient
    client = DeerFlowBridgeClient(base_url="http://localhost:8010")
    print(f"[OK] DeerFlowBridgeClient baslatildi. base_url={client.base_url}")
except Exception as e:
    print(f"[ERR] DeerFlowBridgeClient: {e}")

print("--- [DONE] ---")
