
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from core.debate_engine import DebateEngine, DebateResult, AGENT_PERSONAS, get_debate_engine
from llm.model_router import ModelRouter, TaskComplexity, RoutingDecision, get_model_router
from core.sandbox_runner import SandboxRunner, SandboxResult, get_sandbox_runner
from repair.memory.vector_lessons import VectorLessonsStore, VectorLesson, SimilarLesson, get_vector_lessons
from core.repair_orchestrator import RepairOrchestrator

PASS = 0
FAIL = 1 # Dummy to track

def ok(name):
    print(f"  [OK] {name}")

def fail(name, err=""):
    print(f"  [FAIL] {name} | {err}")

def section(title):
    print(f"\n{'='*55}\n  {title}\n")

# ---- DEBATE ENGINE ----

async def test_agent_personas():
    assert "architect" in AGENT_PERSONAS
    assert "security"  in AGENT_PERSONAS
    assert len(AGENT_PERSONAS) >= 6
    ok("AGENT_PERSONAS tanımlı ve eksiksiz")

async def test_debate_engine_mock():
    engine = DebateEngine(model_orch=None, max_rounds=2)
    result = await engine.run_debate(
        topic="PostgreSQL vs Redis",
        agent_a="backend_dev",
        agent_b="security",
    )
    assert isinstance(result, DebateResult)
    assert len(result.rounds) == 2
    ok("Debate mock modu OK")

async def test_debate_early_agreement():
    class FakeOrch:
        async def complete(self, messages, preferred_agent="general", **kwargs):
            if preferred_agent == "architect":
                return "[UZLAŞI] Tamam."
            return "Argüman."

    engine = DebateEngine(model_orch=FakeOrch(), max_rounds=3)
    result = await engine.run_debate(topic="Test", agent_a="backend_dev", agent_b="devops")
    assert result.agreement_reached is True
    ok("Erken uzlaşı OK")

async def test_debate_to_dict():
    engine = DebateEngine(model_orch=None, max_rounds=1)
    result = await engine.run_debate("test", "qa_engineer", "tech_writer")
    assert "debate_id" in result.to_dict()
    ok("to_dict() OK")

# ---- MODEL ROUTER ----

async def test_complexity_critical_keywords():
    router = ModelRouter()
    d = router.route("Bu security ile ilgili.", "general")
    assert d.complexity == TaskComplexity.CRITICAL
    ok("CRITICAL keyword OK")

async def test_role_based_routing():
    router = ModelRouter()
    d = router.route("Test", "architect")
    assert d.complexity in (TaskComplexity.HIGH, TaskComplexity.CRITICAL)
    ok("Rol bazlı routing OK")

# ---- SANDBOX RUNNER ----

async def test_sandbox_hello_world():
    runner = SandboxRunner(use_docker=False)
    result = await runner.run_python("print('hello')")
    assert result.success
    assert "hello" in result.stdout
    ok("Sandbox Hello World OK")

async def test_sandbox_ast_block_exec():
    runner = SandboxRunner(use_docker=False)
    result = await runner.run_python("exec('print(1)')")
    assert not result.success
    assert result.mode == "ast_blocked"
    ok("Sandbox AST Block OK")

# ---- VECTOR LESSONS ----

async def test_save_and_find():
    store = VectorLessonsStore(use_db=False)
    store.save_lesson(symptom="err", module="auth", resolution="fix", job_id="j", incident_id="i")
    results = store.find_similar("err", module="auth")
    assert len(results) >= 1
    ok("Vector save + find OK")

# ---- ORCHESTRATOR ----

async def test_faz12_methods_bound():
    assert hasattr(RepairOrchestrator, "_step_sandbox_verify")
    ok("RepairOrchestrator methods OK")

# ---- STANDALONE MAIN ----

async def main():
    section("1 — Debate Engine")
    await test_agent_personas()
    await test_debate_engine_mock()
    await test_debate_early_agreement()
    await test_debate_to_dict()

    section("2 — Model Router")
    await test_complexity_critical_keywords()
    await test_role_based_routing()

    section("3 — Sandbox Runner")
    await test_sandbox_hello_world()
    await test_sandbox_ast_block_exec()

    section("4 — Vector Lessons")
    await test_save_and_find()

    section("5 — Orchestrator")
    await test_faz12_methods_bound()

if __name__ == "__main__":
    asyncio.run(main())
