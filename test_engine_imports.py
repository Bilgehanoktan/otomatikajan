
import sys
import os
import traceback

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

report_path = "e:/ai_company_faz12.1/import_test_report.txt"
with open(report_path, "w") as f:
    f.write("--- Starting Engine Import Test ---\n")
    success_count = 0
    for engine_path in engines_to_test:
        module_path, class_name = engine_path.rsplit(".", 1)
        try:
            f.write(f"Testing {module_path}...")
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            f.write(" SUCCESS\n")
            success_count += 1
        except Exception as e:
            f.write(f" FAILED\n")
            f.write(f"Error: {str(e)}\n")
            f.write(traceback.format_exc())
            f.write("\n")

    f.write(f"--- Completed: {success_count}/{len(engines_to_test)} engines loaded successfully ---\n")

print(f"Report written to {report_path}")
sys.exit(0 if success_count == len(engines_to_test) else 1)
