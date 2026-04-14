"""
Resilience Test: Workflow Crash & Recovery (Phase 9.3)
Verifies that the WorkflowEngine can resume from the last successful checkpoint after an interruption.
"""
import asyncio
import os
import sys
import pytest
from datetime import datetime
from uuid import uuid4

# Add project root to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from libs.workflow.models import WorkflowInstance, WorkflowStep, WorkflowStatus, StepStatus
from libs.workflow.engine import WorkflowEngine

# --- Mock Persistence for Unit/Resilience Testing ---
class InMemoryPersistence:
    def __init__(self):
        self.instances = {}
        self.steps = {}
        self.history = {}

    async def save_instance(self, instance):
        self.instances[instance.id] = instance
        print(f"[MockDB] Saved Instance {instance.id} (Status: {instance.status})")

    async def save_step(self, workflow_id, step):
        if workflow_id not in self.steps:
            self.steps[workflow_id] = {}
        self.steps[workflow_id][step.id] = step
        print(f"[MockDB] Saved Step {step.id} (Status: {step.status})")

    async def load_instance(self, workflow_id):
        return self.instances.get(workflow_id)

    async def load_history(self, workflow_id):
        # We simulate history based on step status
        hist = []
        if workflow_id in self.steps:
            for s_id, step in self.steps[workflow_id].items():
                if step.status == StepStatus.COMPLETED:
                    hist.append({"event_type": "step_completed", "step_id": s_id})
        return hist

    async def log_event(self, workflow_id, event_type, details):
        print(f"[MockDB] Logged Event: {event_type} for {workflow_id}")

    async def save_event(self, project_id, event_type, step_id=None, payload=None, operator_id="system"):
        print(f"[MockDB] Saved Event: {event_type} for {project_id} (Step: {step_id})")

@pytest.mark.asyncio
async def test_workflow_crash_recovery():
    print("\n[RESILIENCE] Starting Crash & Recovery Test (Mocked Persistence)...")
    
    # 1. Setup durable engine and MOCKED persistence
    persistence = InMemoryPersistence()
    engine = WorkflowEngine()
    engine.persistence = persistence  # Manual injection
    
    workflow_id = str(uuid4())
    
    # Track execution counts
    counters = {"step_1": 0, "step_2": 0}

    async def step_1_action(ctx, **kw):
        counters["step_1"] += 1
        return {"step_1_done": True}

    async def step_2_action(ctx, **kw):
        counters["step_2"] += 1
        # SIMULATE CRASH: Raise exception only on first attempt
        if counters["step_2"] == 1:
            raise RuntimeError("CRASH SIMULATION: Worker died mid-step")
        return {"step_2_done": True}

    engine.register_action("action_1", step_1_action)
    engine.register_action("action_2", step_2_action)

    steps = [
        WorkflowStep(id="s1", name="step_1", action="action_1", status=StepStatus.PENDING),
        WorkflowStep(id="s2", name="step_2", action="action_2", dependencies=["s1"], status=StepStatus.PENDING, max_retries=0),
    ]
    instance = WorkflowInstance(id=workflow_id, workflow_type="resilience_test", steps=steps, status=WorkflowStatus.PENDING)
    
    # Initial save
    await persistence.save_instance(instance)
    for s in steps:
        await persistence.save_step(workflow_id, s)

    # 2. RUN 1: This will fail at Step 2 (max retries 0)
    print("[RUN 1] Executing workflow until failure...")
    await engine.execute(instance)
    
    # Verify state after failure
    assert instance.status == WorkflowStatus.FAILED
    reloaded = await persistence.load_instance(workflow_id)
    history = await persistence.load_history(workflow_id)
    
    completed_steps = [e["step_id"] for e in history if e["event_type"] == "step_completed"]
    assert "s1" in completed_steps, "Step 1 should be persisted as COMPLETED"
    assert "s2" not in completed_steps, "Step 2 should NOT be persisted as COMPLETED"
    assert counters["step_1"] == 1
    assert counters["step_2"] == 1
    print("[RUN 1] Verified: Step 1 persisted, Step 2 failed correctly.")

    # 3. RUN 2: Recovery (Manual Intervention Simulation)
    print("\n[MANUAL INTERVENTION] Resetting Step 2 to PENDING...")
    instance_recovered = await persistence.load_instance(workflow_id)
    s2 = next(s for s in instance_recovered.steps if s.id == "s2")
    s2.status = StepStatus.PENDING
    instance_recovered.status = WorkflowStatus.RUNNING 
    await persistence.save_step(workflow_id, s2)
    await persistence.save_instance(instance_recovered)

    print("[RUN 2] Resuming workflow from checkpoint...")
    await engine.execute(instance_recovered)
    
    # Final Verification
    assert instance_recovered.status == WorkflowStatus.COMPLETED
    assert counters["step_1"] == 1, "CRITICAL ERROR: Step 1 re-executed! (Idempotency failure)"
    assert counters["step_2"] == 2, "Step 2 should have executed exactly twice (1 fail, 1 success)"
    
    print("\n[FINAL] SUCCESS: Resilience verified.")
    print(f"Counters: {counters}")
    print("[FINAL] Step 1 executed once (skipped in Run 2). Step 2 picked up the work.")

if __name__ == "__main__":
    asyncio.run(test_workflow_crash_recovery())
