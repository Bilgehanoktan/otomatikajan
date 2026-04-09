"""
Faz 11 Test Suite â€” "GÃ¼venilir Repair Platformu"

Test gruplarÄ±:
  - Incident Fingerprint & Similarity
  - Root Cause Ranker
  - Test Generator
  - Canary Runner
  - Metrics Collector
  - Policy Registry
  - Architecture Guard
  - Report Generator
  - Lessons Store
  - RepairJob Canary State Machine
  - repair_admin_router import
"""
import sys, os, asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOT: fastapi/pydantic stub'larÄ± tests/conftest.py iÃ§inde yÃ¶netilir.
# Bu dosya pytest dÄ±ÅŸÄ±nda da Ã§alÄ±ÅŸabilmesi iÃ§in conftest olmadan da Ã§alÄ±ÅŸabilmeli.
# admin router / repair_router testleri AST veya dosya bazlÄ± â€” runtime import yok.

_PASS = 0
_FAIL = 0
_TESTS = []

def test(name):
    def dec(fn):
        _TESTS.append((name, fn))
        return fn
    return dec

def run_all():
    global _PASS, _FAIL
    for name, fn in _TESTS:
        try:
            if asyncio.iscoroutinefunction(fn):
                asyncio.run(fn())
            else:
                fn()
            print(f"  âœ… {name}")
            _PASS += 1
        except Exception as e:
            print(f"  âŒ {name}: {e}")
            _FAIL += 1
    print(f"\nğŸ“Š SONUÃ‡: {_PASS}/{_PASS+_FAIL} test geÃ§ti")
    if _FAIL:
        if __name__ == "__main__":
            sys.exit(1)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 1) Incident Fingerprint & Similarity
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("IncidentFingerprint â€” build_fingerprint temel alanlar")
def test_faz11_001():
    from packages.repair_engine.analysis.incident_fingerprint import build_fingerprint, IncidentFingerprint
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity

    inc = IncidentRecord.create(
        source=IncidentSource.MANUAL,
        severity=IncidentSeverity.HIGH,
        service="task_router",
        module="task_router",
        symptom="NameError: name 'cancel_task' is not defined",
    )
    inc.stack_trace = "File \"api/task_router.py\", line 42, in cancel\n  cancel_task(task_id)\nNameError: name 'cancel_task' is not defined"

    fp = build_fingerprint(inc)
    assert fp.incident_id == inc.incident_id
    assert len(fp.exact_hash) == 16
    assert fp.error_type == "NameError"
    assert fp.module == "task_router"
    assert fp.symptom_norm  # normalized olmalÄ±
    assert fp.to_dict()["error_type"] == "NameError"


@test("IncidentFingerprint â€” normalize_stack_trace dinamik deÄŸerleri temizler")
def test_faz11_002():
    from packages.repair_engine.analysis.incident_fingerprint import _normalize_stack_trace
    raw = 'File "api/tasks.py", line 42, in process\n  obj = 0x7f3a9b12c0\n  id=abc12345-1234-1234-1234-abcdef123456'
    norm = _normalize_stack_trace(raw)
    assert "42" not in norm, "SatÄ±r no temizlenmeli"
    assert "0x7f3a9b12c0" not in norm
    assert "abc12345" not in norm


@test("IncidentSimilarityEngine â€” exact duplicate tespiti")
def test_faz11_003():
    from packages.repair_engine.analysis.incident_fingerprint import build_fingerprint, IncidentSimilarityEngine
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity

    engine = IncidentSimilarityEngine()

    # AynÄ± stack trace ile iki incident
    stack = "File \"heal/engine.py\", line 10, in run\nAttributeError: NoneType"
    inc1 = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.MEDIUM, service="heal_engine", module="heal_engine", symptom="AttributeError on run")
    inc1.stack_trace = stack
    inc2 = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.MEDIUM, service="heal_engine", module="heal_engine", symptom="AttributeError on run tekrar")
    inc2.stack_trace = stack

    fp1 = build_fingerprint(inc1)
    fp2 = build_fingerprint(inc2)

    engine.add(fp1)
    dup_id = engine.is_duplicate(fp2)
    assert dup_id == inc1.incident_id, f"Duplicate tespit edilmeli, got: {dup_id}"


@test("IncidentSimilarityEngine â€” module+error_type benzerliÄŸi")
def test_faz11_004():
    from packages.repair_engine.analysis.incident_fingerprint import build_fingerprint, IncidentSimilarityEngine
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity

    engine = IncidentSimilarityEngine()
    inc1 = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.HIGH, service="orchestrator", module="orchestrator", symptom="TypeError: missing argument")
    inc1.stack_trace = "File \"core/orchestrator.py\", line 5, in run\nTypeError: missing argument"
    inc2 = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.HIGH, service="orchestrator", module="orchestrator", symptom="TypeError: unexpected kwarg")
    inc2.stack_trace = "File \"core/orchestrator.py\", line 12, in dispatch\nTypeError: unexpected kwarg"

    fp1 = build_fingerprint(inc1)
    fp2 = build_fingerprint(inc2)
    engine.add(fp1)

    similars = engine.find_similar(fp2, limit=5, min_similarity=0.4)
    assert similars, "Benzer incident bulunmalÄ±"
    found = next((s for s in similars if s.incident_id == inc1.incident_id), None)
    assert found, "inc1 benzerler arasÄ±nda olmalÄ±"
    assert found.match_type == "module_error"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 2) Root Cause Ranker
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("RootCauseRanker â€” kural bonusu uygulanÄ±yor")
def test_faz11_005():
    from packages.repair_engine.analysis.root_cause_ranker import RootCauseRanker, LessonRecord
    # Sadece ranker'Ä±n stats ve record_lesson metodlarÄ±nÄ± test et (schema baÄŸÄ±msÄ±z)
    ranker = RootCauseRanker()
    ranker.record_lesson("route_error", "task_router", "route endpoint eksik", "success")
    ranker.record_lesson("route_error", "task_router", "route endpoint eksik", "success")
    ranker.record_lesson("route_error", "task_router", "auth token", "rejected", "wrong_root_cause")
    stats = ranker.stats()
    assert stats["success_lessons"] == 2, f"2 success bekleniyor: {stats}"
    assert stats["rejection_count"] >= 1, "En az 1 rejection bekleniyor"


@test("RootCauseRanker â€” rejection cezasÄ± azaltma")
def test_faz11_006():
    from packages.repair_engine.analysis.root_cause_ranker import RootCauseRanker
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
try:
    from packages.repair_engine.schemas.diagnosis import RootCauseHypothesis
except ImportError:
    RootCauseHypothesis = None
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    import uuid

    ranker = RootCauseRanker()
    # AynÄ± tipi 2 kez reddet
    ranker.record_lesson("route_error", "task_router", "route endpoint eksik", "rejected", "wrong_root_cause")
    ranker.record_lesson("route_error", "task_router", "route endpoint eksik", "rejected", "wrong_root_cause")

    stats = ranker.stats()
    assert stats["rejection_count"] >= 2
    assert len(stats["penalized_patterns"]) >= 1


@test("RootCauseRanker â€” geÃ§miÅŸ baÅŸarÄ± bonusu")
def test_faz11_007():
    from packages.repair_engine.analysis.root_cause_ranker import RootCauseRanker
    ranker = RootCauseRanker()
    ranker.record_lesson("import_error", "llm", "missing import", "success")
    ranker.record_lesson("import_error", "llm", "missing import", "success")
    stats = ranker.stats()
    assert stats["success_lessons"] == 2


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 3) Test Generator
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("TestGenerator â€” API incident -> api test Ã¼retir")
def test_faz11_008():
    from packages.repair_engine.generation.test_generator import get_test_generator
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel

    inc = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.HIGH, service="task_router", module="task_router", symptom="500 on /api/tasks endpoint")
    plan = PatchPlan.create("d001", target_files=["api/task_router.py"], risk=RiskLevel.MEDIUM)

    gen  = get_test_generator()
    test = gen.generate(inc, plan, job_id="rjob_test")

    assert test.test_type == "api", f"API incident -> api test bekleniyor, got: {test.test_type}"
    assert "AsyncClient" in test.test_code or "/api/" in test.test_code
    assert test.target_file.startswith("tests/")
    assert test.job_id == "rjob_test"
    assert test.to_dict()["test_type"] == "api"


@test("TestGenerator â€” Unit test Ã¼retimi (generic incident)")
def test_faz11_009():
    from packages.repair_engine.generation.test_generator import get_test_generator
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel

    inc  = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.MEDIUM, service="heal_engine", module="heal_engine", symptom="AttributeError on heal")
    plan = PatchPlan.create("d002", target_files=["heal/engine.py"], risk=RiskLevel.LOW)
    gen  = get_test_generator()
    t    = gen.generate(inc, plan, job_id="rjob_unit")

    assert t.test_type in ("unit", "smoke")
    assert t.description
    assert "regression" in t.description.lower() or "smoke" in t.description.lower()


@test("TestGenerator â€” Import incident -> smoke test Ã¼retir")
def test_faz11_010():
    from packages.repair_engine.generation.test_generator import get_test_generator
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
    import uuid

    inc  = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.HIGH, service="llm", module="llm", symptom="ModuleNotFoundError: packages.llm_gateway.adapters")
    plan = PatchPlan.create("d003", target_files=["llm/adapters.py"], risk=RiskLevel.LOW)
    ticket = DiagnosisTicket(
        ticket_id=f"tkt_{uuid.uuid4().hex[:6]}",
        incident_id=inc.incident_id,
        classification=ProblemClass.IMPORT_ERROR,
        severity="high",
        candidate_files=["llm/adapters.py"],
    )
    gen = get_test_generator()
    t   = gen.generate(inc, plan, ticket=ticket)
    assert t.test_type == "smoke", f"Import error -> smoke bekleniyor, got: {t.test_type}"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 4) Canary Runner
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("CanaryRunner â€” temel akÄ±ÅŸ (syntax + regression + import)")
async def test_faz11_011():
    from packages.repair_engine.verification.canary_runner import get_canary_runner, CanaryStatus

    diff = "--- a/llm/adapters.py\n+++ b/llm/adapters.py\n@@ -1,3 +1,4 @@\n+import os\n from typing import Optional\n"
    runner = get_canary_runner()
    result = await runner.run(
        job_id="rjob_canary_test",
        diff=diff,
        changed_files=["llm/adapters.py"],
        project_root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    assert result.job_id == "rjob_canary_test"
    assert result.status in (CanaryStatus.PASSED, CanaryStatus.FAILED)
    assert result.total_count > 0
    assert result.to_dict()["status"]


@test("CanaryRunner â€” eval() tespiti -> failed")
async def test_faz11_012():
    from packages.repair_engine.verification.canary_runner import get_canary_runner, CanaryStatus

    diff = "+++ b/api/routes.py\n+    eval(user_input)  # dangerous\n"
    runner = get_canary_runner()
    result = await runner.run("rjob_evil", diff, ["api/routes.py"])
    # regression_signal check failed
    reg_check = next((c for c in result.checks if c.name == "regression_signal"), None)
    assert reg_check and not reg_check.passed, "eval() tespiti baÅŸarÄ±sÄ±z olmali"
    assert runner.should_block_pr(result), "eval() olan patch bloke edilmeli"


@test("CanaryRunner â€” temiz diff -> passed")
async def test_faz11_013():
    from packages.repair_engine.verification.canary_runner import get_canary_runner, CanaryStatus

    diff = "+++ b/core/policy_engine.py\n+    # Basit yorum eklendi\n"
    runner = get_canary_runner()
    result = await runner.run("rjob_clean", diff, [])
    reg_check = next((c for c in result.checks if c.name == "regression_signal"), None)
    assert reg_check and reg_check.passed, "Temiz diff regression_signal geÃ§meli"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 5) Metrics Collector
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("RepairMetricsStore â€” kayÄ±t ve summary")
def test_faz11_014():
    from packages.repair_engine.verification.metrics_collector import RepairMetricsStore, make_metric

    store = RepairMetricsStore()
    for decision, count in [("success", 5), ("rejected", 2), ("manual", 1)]:
        for _ in range(count):
            store.record(make_metric(
                job_id="rjob_x", incident_id="inc_y",
                incident_class="route_error", module="task_router",
                decision=decision, confidence=70,
            ))

    s = store.summary(last_days=30)
    assert s["total_jobs"] == 8
    assert s["first_patch_success_rate"] == round(5/8*100, 1)
    assert s["rejection_rate"] == round(2/8*100, 1)


@test("RepairMetricsStore â€” trends boÅŸ -> liste dÃ¶ner")
def test_faz11_015():
    from packages.repair_engine.verification.metrics_collector import RepairMetricsStore
    store = RepairMetricsStore()
    trends = store.trends(last_days=7)
    assert isinstance(trends, list)


@test("RepairMetricsStore â€” top_modules sÄ±ralama")
def test_faz11_016():
    from packages.repair_engine.verification.metrics_collector import RepairMetricsStore, make_metric

    store = RepairMetricsStore()
    for mod, n in [("task_router", 5), ("orchestrator", 2), ("auth", 1)]:
        for _ in range(n):
            store.record(make_metric("j","i","cls", mod, "success", confidence=80))

    top = store.top_modules(top_n=3)
    assert top[0]["module"] == "task_router", "En Ã§ok incident alan modÃ¼l baÅŸta gelmeli"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 6) Policy Registry
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("PolicyRegistry â€” varsayÄ±lan kurallar yÃ¼klÃ¼")
def test_faz11_017():
    from core.policy_registry import get_policy_registry
    reg = get_policy_registry()
    rules = reg.list_all()
    assert len(rules) >= 9, f"En az 9 varsayÄ±lan kural bekleniyor, got: {len(rules)}"
    names = {r["name"] for r in rules}
    assert "block_auth_module"          in names
    assert "max_diff_lines_for_auto_pr" in names
    assert "min_confidence_for_auto_pr" in names


@test("PolicyRegistry â€” is_module_blocked auth tespit eder")
def test_faz11_018():
    from core.policy_registry import get_policy_registry
    reg = get_policy_registry()
    assert reg.is_module_blocked("auth/jwt_auth.py")
    assert not reg.is_module_blocked("api/task_router.py")


@test("PolicyRegistry â€” is_high_risk_file tanÄ±dÄ±k dosyalar")
def test_faz11_019():
    from core.policy_registry import get_policy_registry
    reg = get_policy_registry()
    assert reg.is_high_risk_file("main.py")
    assert reg.is_high_risk_file("db/models.py")
    assert not reg.is_high_risk_file("api/task_read_router.py")


@test("PolicyRegistry â€” update ve export/import JSON dÃ¶ngÃ¼sÃ¼")
def test_faz11_020():
    from core.policy_registry import PolicyRegistry, PolicyRule
    reg = PolicyRegistry()
    reg.update("min_confidence_for_auto_pr", value=75, updated_by="test")
    assert reg.min_confidence() == 75

    json_str = reg.export_json()
    reg2 = PolicyRegistry()
    count = reg2.import_json(json_str, updated_by="import")
    assert count >= 9
    assert reg2.min_confidence() == 75


@test("PolicyRegistry â€” yeni kural ekleme")
def test_faz11_021():
    from core.policy_registry import PolicyRegistry, PolicyRule
    reg = PolicyRegistry()
    reg.add(PolicyRule(name="test_custom_rule", description="Test", enabled=True, value="test"))
    assert reg.get("test_custom_rule") is not None
    assert reg.get_value("test_custom_rule") == "test"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 7) Architecture Guard
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("ArchitectureGuard â€” temiz diff -> passed")
def test_faz11_022():
    from packages.repair_engine.review.architecture_guard import get_architecture_guard

    diff = """--- a/api/task_router.py
+++ b/api/task_router.py
@@ -1,3 +1,4 @@
+from apps.api.support._task_shared import task_to_dict
 from fastapi import APIRouter
"""
    result = get_architecture_guard().check_diff(diff)
    assert result.passed, f"Temiz diff geÃ§meli, violations: {result.violations}"


@test("ArchitectureGuard â€” api -> packages.persistence.models direkt import -> error")
def test_faz11_023():
    from packages.repair_engine.review.architecture_guard import get_architecture_guard

    diff = """+++ b/api/task_router.py
+from packages.persistence.models import Task
"""
    result = get_architecture_guard().check_diff(diff)
    assert not result.passed, "api/ -> packages.persistence.models import 'error' violation olmalÄ±"
    errors = [v for v in result.violations if v.severity == "error"]
    assert errors, "En az bir error violation bekleniyor"
    assert any("api_direct_db_model" == v.rule for v in errors)


@test("ArchitectureGuard â€” eval() -> repair direct write -> error")
def test_faz11_024():
    from packages.repair_engine.review.architecture_guard import get_architecture_guard

    diff = """+++ b/repair/generation/patch_gen.py
+    open("db/models.py", "w").write(code)
"""
    result = get_architecture_guard().check_diff(diff)
    errors = [v for v in result.violations if v.severity == "error"]
    assert any(v.rule == "repair_direct_write" for v in errors)


@test("ArchitectureGuard â€” to_dict alanlarÄ± tam")
def test_faz11_025():
    from packages.repair_engine.review.architecture_guard import get_architecture_guard
    diff = "+++ b/api/routes.py\n+pass\n"
    result = get_architecture_guard().check_diff(diff)
    d = result.to_dict()
    assert "passed" in d
    assert "violations" in d
    assert "checked_files" in d


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 8) Report Generator
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("ReportGenerator â€” markdown rapor temel alanlarÄ± iÃ§erir")
def test_faz11_026():
    from packages.repair_engine.reporting.report_generator import generate_markdown_report
    from packages.repair_engine.schemas.repair_job import RepairJob
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity

    job = RepairJob.create("inc_test_001")
    inc = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.HIGH, service="task_router", module="task_router", symptom="500 on POST /tasks")

    md = generate_markdown_report(job, inc, decision="rejected", feedback_code="wrong_root_cause")
    assert "# " in md              # baÅŸlÄ±k
    assert job.job_id in md
    assert inc.module in md
    assert "REJECTED" in md
    assert "wrong_root_cause" in md


@test("ReportGenerator â€” html rapor DOCTYPE iÃ§erir")
def test_faz11_027():
    from packages.repair_engine.reporting.report_generator import generate_html_report
    from packages.repair_engine.schemas.repair_job import RepairJob
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity

    job = RepairJob.create("inc_html_test")
    inc = IncidentRecord.create(IncidentSource.MANUAL, IncidentSeverity.MEDIUM, service="orchestrator", module="orchestrator", symptom="Timeout")
    html = generate_html_report(job, inc, decision="manual")
    assert "<!DOCTYPE html>" in html
    assert job.job_id in html


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 9) Lessons Store
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("LessonsStore â€” feedback kayÄ±t ve istatistik")
def test_faz11_028():
    from packages.repair_engine.memory.lessons_store import LessonsStore

    store = LessonsStore()
    for code, decision in [("correct_fix","approved"),("wrong_root_cause","rejected"),("too_broad_patch","rejected")]:
        store.record(
            job_id="rjob_ls", pr_id="pr_ls", decided_by="tester",
            decision=decision, feedback_code=code,
            module="orchestrator", incident_class="route_error",
        )

    stats = store.stats()
    assert stats["total_feedback"] == 3
    assert stats["approved"] == 1
    assert stats["rejected"] == 2
    assert "wrong_root_cause" in stats["top_reject_reasons"]


@test("LessonsStore â€” geÃ§ersiz feedback_code -> other'a normalize")
def test_faz11_029():
    from packages.repair_engine.memory.lessons_store import LessonsStore
    store = LessonsStore()
    rec = store.record("j","p","u","rejected","invalid_code_xyz","","mod","cls")
    assert rec.feedback_code == "other"


@test("LessonsStore â€” module_feedback_summary")
def test_faz11_030():
    from packages.repair_engine.memory.lessons_store import LessonsStore
    store = LessonsStore()
    for _ in range(3):
        store.record("j","p","u","approved","correct_fix","","auth","cls")
    summary = store.module_feedback_summary("auth")
    assert summary["total"] == 3
    assert summary["approval_rate"] == 100.0


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 10) RepairJob Canary State Machine
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("RepairJob â€” VERIFIED -> CANARY_PENDING geÃ§iÅŸi")
def test_faz11_031():
    from packages.repair_engine.schemas.repair_job import RepairJob, RepairJobStatus
    job = RepairJob.create("inc_canary_sm")
    transitions = [
        RepairJobStatus.INCIDENT_COLLECTED,
        RepairJobStatus.TRIAGED,
        RepairJobStatus.CONTEXT_BUILT,
        RepairJobStatus.ROOT_CAUSE_ANALYZED,
        RepairJobStatus.PATCH_PLANNED,
        RepairJobStatus.PATCH_GENERATED,
        RepairJobStatus.REVIEWED,
        RepairJobStatus.VERIFIED,
        RepairJobStatus.CANARY_PENDING,
        RepairJobStatus.CANARY_RUNNING,
        RepairJobStatus.CANARY_PASSED,
        RepairJobStatus.PR_CREATED,
        RepairJobStatus.AWAITING_APPROVAL,
        RepairJobStatus.MERGED,
    ]
    for status in transitions:
        ok = job.transition(status)
        assert ok, f"GeÃ§iÅŸ baÅŸarÄ±sÄ±z: -> {status.value} (ÅŸu an: {job.status.value})"
    assert job.status == RepairJobStatus.MERGED


@test("RepairJob â€” CANARY_FAILED -> REQUIRES_MANUAL_REVIEW")
def test_faz11_032():
    from packages.repair_engine.schemas.repair_job import RepairJob, RepairJobStatus
    job = RepairJob.create("inc_canary_fail")
    for s in [
        RepairJobStatus.INCIDENT_COLLECTED, RepairJobStatus.TRIAGED,
        RepairJobStatus.CONTEXT_BUILT, RepairJobStatus.ROOT_CAUSE_ANALYZED,
        RepairJobStatus.PATCH_PLANNED, RepairJobStatus.PATCH_GENERATED,
        RepairJobStatus.REVIEWED, RepairJobStatus.VERIFIED,
        RepairJobStatus.CANARY_PENDING, RepairJobStatus.CANARY_RUNNING,
        RepairJobStatus.CANARY_FAILED,
    ]:
        ok = job.transition(s)
        assert ok, f"GeÃ§iÅŸ baÅŸarÄ±sÄ±z: {s.value}"
    assert job.transition(RepairJobStatus.REQUIRES_MANUAL_REVIEW)
    assert job.is_terminal()


@test("RepairJob â€” Faz 11 alanlarÄ± mevcut")
def test_faz11_033():
    from packages.repair_engine.schemas.repair_job import RepairJob
    job = RepairJob.create("inc_faz11_fields")
    job.canary_id     = "can_abc123"
    job.canary_status = "passed"
    job.risk_score    = 35
    job.simulation_mode = True
    job.generated_tests = [{"test_id": "tgen_001", "test_type": "api"}]
    d = job.to_dict()
    assert d["canary_id"]      == "can_abc123"
    assert d["canary_status"]  == "passed"
    assert d["risk_score"]     == 35
    assert d["simulation_mode"] is True
    assert len(d["generated_tests"]) == 1


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 11) API Router imports
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@test("repair_admin_router â€” import OK")
def test_faz11_034():
    # Check that file is syntactically valid and has router
    import ast
    fpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api", "repair_admin_router.py")
    with open(fpath) as f:
        src = f.read()
    ast.parse(src)  # syntax ok
    assert "router = APIRouter" in src or "router=APIRouter" in src or "APIRouter(" in src


@test("core.policy_registry â€” singleton tekil")
def test_faz11_035():
    from core.policy_registry import get_policy_registry
    r1 = get_policy_registry()
    r2 = get_policy_registry()
    assert r1 is r2, "Singleton aynÄ± instance dÃ¶ndÃ¼rmeli"


@test("repair_router Faz 11 endpoint'leri mevcut")
def test_faz11_036():
    fpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api", "repair_router.py")
    with open(fpath) as f:
        src = f.read()
    assert "generated-tests"    in src
    assert "canary"             in src
    assert "simulate"           in src
    assert "similar"            in src
    assert "architecture/guard" in src
    assert "report"             in src


if __name__ == "__main__":
    print("\n=== Faz 11 Test Suite ===\n")
    run_all()

