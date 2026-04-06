
import sys
import os

# Ensure e:/ai_company_faz12.1 is in sys.path
root = "e:/ai_company_faz12.1"
if root not in sys.path:
    sys.path.insert(0, root)

engines_to_test = [
    "packages.orchestration.agi.operational.velocity_engine.VelocityEngine",
    "packages.orchestration.agi.cognitive.metacognitive_auditor.MetacognitiveAuditor",
    "packages.orchestration.agi.cognitive.synaptic_cortex.UnifiedGalacticCortex",
    "packages.llm_gateway.model_orchestrator.ModelOrchestrator",
    "packages.persistence.session.session_scope",
]

print("--- Starting Engine Import Test ---")
success_count = 0
for engine_path in engines_to_test:
    module_path, class_name = engine_path.rsplit(".", 1)
    try:
        print(f"Testing {module_path}...", end=" ")
        module = __import__(module_path, fromlist=[class_name])
        getattr(module, class_name)
        print("SUCCESS")
        success_count += 1
    except Exception as e:
        print(f"FAILED: {e}")

print(f"--- Completed: {success_count}/{len(engines_to_test)} engines loaded successfully ---")
sys.exit(0 if success_count == len(engines_to_test) else 1)
