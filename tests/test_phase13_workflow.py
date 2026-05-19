"""
Phase 13.04 Test Suite — Workflow Engine & Control Plane API
Offline (no DB/Redis) unit tests.
"""
import asyncio
import sys
import os
import traceback
import uuid
from datetime import datetime

# Add project root to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

PASS = 0
FAIL = 0

def ok(name):
    global PASS
    PASS += 1
    print(f"  PASS  {name}")

def fail(name, reason):
    global FAIL
    FAIL += 1
    print(f"  FAIL  {name}: {reason}")

class MockPersistence:
    def __init__(self, initial_inst=None):
        self.inst = initial_inst
    async def save_instance(self, inst): self.inst = inst
    async def save_step(self, inst_id, step): pass
    async def load_instance(self, inst_id): return self.inst
    async def save_event(self, project_id, event_type, step_id=None, payload=None): pass
    async def load_history(self, project_id): return []

# ─────────────────────────────────────────────────────────────
# 1. Model imports & field validation
# ─────────────────────────────────────────────────────────────
def test_models():
    try:
        from libs.workflow.models import (
            WorkflowInstance, WorkflowStep,
            WorkflowStatus, StepStatus
        )

        step = WorkflowStep(
            id="step-1", name="plan", action="plan_subtasks",
            input_data={"title": "test"}, dependencies=["dep-1"]
        )
        assert step.status == StepStatus.PENDING
        assert step.retries == 0
        assert step.max_retries == 3
        assert step.dependencies == ["dep-1"]
        ok("WorkflowStep fields")

        inst = WorkflowInstance(
            id="inst-1", workflow_type="default",
            steps=[step]
        )
        assert inst.status == WorkflowStatus.PENDING
        assert len(inst.steps) == 1
        ok("WorkflowInstance fields")

    except Exception as e:
        fail("models", str(e))

# ─────────────────────────────────────────────────────────────
# 2. WorkflowEngine — in-memory execution (no DB)
# ─────────────────────────────────────────────────────────────
def test_engine_inmemory():
    try:
        from libs.workflow.models import (
            WorkflowInstance, WorkflowStep,
            WorkflowStatus, StepStatus
        )
        from libs.workflow.engine import WorkflowEngine
        
        engine = WorkflowEngine()
        # Three steps: A || C -> B (B depends on A; C is independent)
        steps = [
            WorkflowStep(id="s1", name="step_a", action="action_a", dependencies=[]),
            WorkflowStep(id="s2", name="step_b", action="action_b", dependencies=["s1"]),
            WorkflowStep(id="s3", name="step_c", action="action_c", dependencies=[]),
        ]
        inst = WorkflowInstance(id="test-inst", workflow_type="test", steps=steps)
        
        engine.persistence = MockPersistence(inst)

        # Register test actions
        call_log = []
        async def action_a(ctx, **kw):
            call_log.append("a")
            return {"_context_update": {"a_done": True}}

        async def action_b(ctx, **kw):
            assert ctx.get("a_done"), "a_done must be in context before b runs"
            call_log.append("b")
            return {"result": "b_result"}

        async def action_c(ctx, **kw):
            call_log.append("c")
            return {"result": "c_result"}

        engine.register_action("action_a", action_a)
        engine.register_action("action_b", action_b)
        engine.register_action("action_c", action_c)

        asyncio.run(engine.execute(inst))

        assert inst.status == WorkflowStatus.COMPLETED, f"Expected COMPLETED, got {inst.status}"
        ok("WorkflowEngine: linear + parallel execution")

        assert "a" in call_log
        assert "b" in call_log
        assert "c" in call_log
        ok("WorkflowEngine: all steps executed")

        # Verify context propagation: a ran before b
        a_idx = call_log.index("a")
        b_idx = call_log.index("b")
        assert a_idx < b_idx, "step_a must complete before step_b"
        ok("WorkflowEngine: dependency ordering respected")

        for s in inst.steps:
            assert s.status == StepStatus.COMPLETED, f"Step {s.name} status: {s.status}"
        ok("WorkflowEngine: all steps COMPLETED")

    except Exception as e:
        fail("engine_inmemory", f"{e}\n{traceback.format_exc()}")

# ─────────────────────────────────────────────────────────────
# 3. WorkflowEngine — retry on failure
# ─────────────────────────────────────────────────────────────
def test_engine_retry():
    try:
        from libs.workflow.models import (
            WorkflowInstance, WorkflowStep,
            WorkflowStatus, StepStatus
        )
        from libs.workflow.engine import WorkflowEngine
        
        engine = WorkflowEngine()
        step = WorkflowStep(id="s1", name="flaky_step", action="flaky", max_retries=3)
        inst = WorkflowInstance(id="retry-test", workflow_type="test", steps=[step])
        engine.persistence = MockPersistence(inst)

        call_count = [0]
        async def flaky_action(ctx, **kw):
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Simulated transient failure")
            return {"result": "ok_on_third_try"}

        engine.register_action("flaky", flaky_action)

        asyncio.run(engine.execute(inst))

        assert inst.status == WorkflowStatus.COMPLETED, f"Expected COMPLETED after retries, got {inst.status}"
        assert call_count[0] == 3, f"Expected 3 calls, got {call_count[0]}"
        ok("WorkflowEngine: retries on transient failure")

    except Exception as e:
        fail("engine_retry", f"{e}\n{traceback.format_exc()}")

# ─────────────────────────────────────────────────────────────
# 4. WorkflowEngine — permanent failure propagates
# ─────────────────────────────────────────────────────────────
def test_engine_permanent_failure():
    try:
        from libs.workflow.models import (
            WorkflowInstance, WorkflowStep,
            WorkflowStatus, StepStatus
        )
        from libs.workflow.engine import WorkflowEngine
        
        engine = WorkflowEngine()
        step = WorkflowStep(id="s1", name="bad_step", action="always_fail", max_retries=0)
        inst = WorkflowInstance(id="fail-test", workflow_type="test", steps=[step])
        engine.persistence = MockPersistence(inst)

        async def always_fail(ctx, **kw):
            raise RuntimeError("Hard failure")

        engine.register_action("always_fail", always_fail)

        asyncio.run(engine.execute(inst))

        assert inst.status == WorkflowStatus.FAILED, f"Expected FAILED, got {inst.status}"
        assert inst.steps[0].status == StepStatus.FAILED
        ok("WorkflowEngine: permanent failure -> FAILED status")

    except Exception as e:
        fail("engine_permanent_failure", f"{e}\n{traceback.format_exc()}")

# ─────────────────────────────────────────────────────────────
# 5. WorkflowEngine — deadlock detection
# ─────────────────────────────────────────────────────────────
def test_engine_deadlock():
    try:
        from libs.workflow.models import (
            WorkflowInstance, WorkflowStep,
            WorkflowStatus, StepStatus
        )
        from libs.workflow.engine import WorkflowEngine
        
        engine = WorkflowEngine()
        # Step depends on non-existent step -> deadlock
        step = WorkflowStep(id="s1", name="deadlock_step", action="dummy", dependencies=["non-existent"])
        inst = WorkflowInstance(id="deadlock-test", workflow_type="test", steps=[step])
        engine.persistence = MockPersistence(inst)

        async def dummy(ctx, **kw): return {}
        engine.register_action("dummy", dummy)

        asyncio.run(engine.execute(inst))

        assert inst.status == WorkflowStatus.FAILED, f"Expected FAILED on deadlock, got {inst.status}"
        ok("WorkflowEngine: deadlock -> FAILED status")

    except Exception as e:
        fail("engine_deadlock", f"{e}\n{traceback.format_exc()}")

# ─────────────────────────────────────────────────────────────
# 6. WorkflowRunner — build_project_workflow
# ─────────────────────────────────────────────────────────────
def test_runner_build():
    try:
        from libs.workflow.runner import build_project_workflow
        from libs.workflow.models import WorkflowStatus

        # 1. Default Template
        p1_id = str(uuid.uuid4())
        i1 = build_project_workflow(p1_id, "P1", "D1", workflow_template="default")
        assert len(i1.steps) == 3
        assert i1.steps[0].name == "plan"
        assert i1.steps[1].name == "execute"
        assert i1.steps[2].name == "report"
        ok("Runner: default template steps generated")

        # 2. Research Template
        p2_id = str(uuid.uuid4())
        i2 = build_project_workflow(p2_id, "P2", "D2", workflow_template="research")
        assert len(i2.steps) == 3
        assert i2.steps[0].name == "research_plan"
        assert "strategy" in i2.steps[0].input_data
        ok("Runner: research template steps generated")

    except Exception as e:
        fail("runner_build", f"{e}\n{traceback.format_exc()}")

# ─────────────────────────────────────────────────────────────
# 7. API Router — importable and route count check
# ─────────────────────────────────────────────────────────────
def test_api_router_import():
    try:
        from services.workflow_api.router import router
        routes = [r for r in router.routes]
        assert len(routes) >= 5, f"Expected >=5 routes, got {len(routes)}"
        paths = [r.path for r in routes if hasattr(r, 'path')]
        assert any("stats" in p for p in paths), "Missing stats route"
        assert any("replay" in p for p in paths), "Missing replay route"
        assert any("cancel" in p for p in paths), "Missing cancel route"
        assert any("reassign" in p for p in paths), "Missing reassign route"
        assert any("approve" in p for p in paths), "Missing approve route"
        ok(f"Workflow API Router: {len(routes)} routes validated")
    except Exception as e:
        fail("api_router_import", f"{e}\n{traceback.format_exc()}")

# ─────────────────────────────────────────────────────────────
# Run All Tests
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Phase 13.04 Test Suite (Refactored)")
    print("=" * 60)

    test_models()
    test_engine_inmemory()
    test_engine_retry()
    test_engine_permanent_failure()
    test_engine_deadlock()
    test_runner_build()
    test_api_router_import()

    print()
    print("=" * 60)
    total = PASS + FAIL
    print(f"RESULT: {PASS}/{total} passed  |  {FAIL} failed")
    print("=" * 60)
    sys.exit(0 if FAIL == 0 else 1)
