import asyncio
import os
import json
import uuid
from services.orchestration.agi.cognitive.policy_evolution import PolicyEvolutionEngine
from services.orchestration.agi.cognitive.goal_synthesizer import GoalSynthesizer
from services.orchestration.governance.policy_engine import policy_engine, AutomationLevel

async def verify_metacognitive_layer():
    print("--- Phase 18 Metacognitive Verification ---")
    
    # 1. PolicyEngine JSON Load Check
    print(f"[*] Checking PolicyEngine... Max Automation: {policy_engine.max_automation.name}")
    assert policy_engine.max_automation == AutomationLevel.CREATE_PR
    assert "confidence_min" in policy_engine.thresholds
    print("[SUCCESS] PolicyEngine dynamic load OK.")

    # 2. Policy Evolution Engine Initialization
    print("[*] Initializing PolicyEvolutionEngine...")
    pe_engine = PolicyEvolutionEngine()
    # Simulate a drift update
    pe_engine.policy_engine.evolve_policy({"thresholds": {"confidence_min": 61}})
    print(f"[*] Policy Evolution check: New Confidence Threshold = {policy_engine.thresholds['confidence_min']}")
    assert policy_engine.thresholds["confidence_min"] == 61
    print("[SUCCESS] Policy Evolution link OK.")

    # 3. Goal Synthesizer Initialization
    print("[*] Initializing GoalSynthesizer...")
    gs_engine = GoalSynthesizer()
    print("[SUCCESS] GoalSynthesizer initialization OK.")

    from services.orchestration.agi.security.audit_gate import AuditGate
    from libs.llm.model_orchestrator import ModelOrchestrator
    gate = AuditGate(ModelOrchestrator())
    # This just checks if it imports and accesses correctly without crashing
    print("[SUCCESS] AuditGate cross-link OK.")

    print("\n[PHASE 18] ALL COGNITIVE NODES VERIFIED.")

if __name__ == "__main__":
    asyncio.run(verify_metacognitive_layer())
