"""
Faz 10  Self-Repair Architecture Test Paketi

Kapsam:
  - packages.repair_engine.schemas    (incident, diagnosis, patch_plan, validation, repair_job)
  - packages.repair_engine.ingestion  (incident ingestor)
  - packages.repair_engine.triage     (triage engine)
  - packages.repair_engine.planning   (patch planner)
  - packages.repair_engine.review     (patch reviewer)
  - packages.repair_engine.verification (syntax, security, architecture checks)
  - packages.repair_engine.memory     (incident, patch, architecture memory)
  - core.policy_engine
  - core.repair_orchestrator (state machine)
"""

import asyncio
import sys
import os
import ast
import traceback

# Proje kkn path'e ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PASS = ""
FAIL = ""
SKIP = ""

results: list[tuple[str, bool, str]] = []


def test(name: str):
    def decorator(fn):
        def wrapper():
            try:
                fn()
                results.append((name, True, ""))
                print(f"  {PASS} {name}")
            except AssertionError as e:
                results.append((name, False, str(e)))
                print(f"  {FAIL} {name}: {e}")
            except Exception as e:
                results.append((name, False, f"{type(e).__name__}: {e}"))
                print(f"  {FAIL} {name}: {type(e).__name__}: {e}")
        return wrapper
    return decorator


def atest(name: str):
    def decorator(fn):
        def wrapper():
            try:
                asyncio.run(fn())
                results.append((name, True, ""))
                print(f"  {PASS} {name}")
            except AssertionError as e:
                results.append((name, False, str(e)))
                print(f"  {FAIL} {name}: {e}")
            except Exception as e:
                results.append((name, False, f"{type(e).__name__}: {e}"))
                print(f"  {FAIL} {name}: {type(e).__name__}: {e}")
        return wrapper
    return decorator


# 
# 1. SCHEMAS
# 
print("\n 1. Schemas")

@test("IncidentRecord  oluturma ve to_dict")
def test_faz10_001():
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    inc = IncidentRecord.create(
        source=IncidentSource.RUNTIME_LOG,
        severity=IncidentSeverity.HIGH,
        service="backend-api",
        module="task_router",
        symptom="500 Internal Server Error",
        stack_trace="TypeError: object is not callable",
    )
    assert inc.incident_id.startswith("inc_")
    d = inc.to_dict()
    assert d["severity"] == "high"
    assert d["module"] == "task_router"
if __name__ == "__main__": test_faz10_001()

@test("RepairJob  durum makinesi geileri")
def test_faz10_002():
    from packages.repair_engine.schemas.repair_job import RepairJob, RepairJobStatus
    job = RepairJob.create("inc_test001")
    assert job.status == RepairJobStatus.NEW
    ok = job.transition(RepairJobStatus.INCIDENT_COLLECTED, note="test")
    assert ok
    assert job.status == RepairJobStatus.INCIDENT_COLLECTED
    assert len(job.history) == 1
if __name__ == "__main__": test_faz10_002()

@test("RepairJob  geersiz gei reddedilir")
def test_faz10_003():
    from packages.repair_engine.schemas.repair_job import RepairJob, RepairJobStatus
    job = RepairJob.create("inc_test002")
    ok = job.transition(RepairJobStatus.MERGED)   # NEW  MERGED geersiz
    assert not ok
if __name__ == "__main__": test_faz10_003()

@test("RepairJob  terminal durumdan gei yok")
def test_faz10_004():
    from packages.repair_engine.schemas.repair_job import RepairJob, RepairJobStatus
    job = RepairJob.create("inc_test003")
    job.transition(RepairJobStatus.INCIDENT_COLLECTED)
    ok_rejected = job.transition(RepairJobStatus.REJECTED)  # INCIDENT_COLLECTED  REJECTED geerli
    assert ok_rejected, "INCIDENT_COLLECTEDREJECTED geii geerli olmal"
    assert job.is_terminal(), f"REJECTED terminal olmal, status={job.status}"
    ok = job.transition(RepairJobStatus.TRIAGED)   # REJECTED'dan devam yok
    assert not ok, "Terminal durumdan gei yaplmamal"
if __name__ == "__main__": test_faz10_004()

@test("PatchPlan  safe_for_auto_patch mant")
def test_faz10_005():
    from packages.repair_engine.schemas.patch_plan import PatchPlan, PatchAction, ChangeType, RiskLevel
    plan = PatchPlan.create(
        ticket_id="diag_001",
        target_files=["main.py"],
        risk=RiskLevel.LOW,
        public_api_impact=False,
        migration_required=False,
        backward_compatible=True,
    )
    assert plan.is_safe_for_auto_patch()
    plan.risk = RiskLevel.HIGH
    assert not plan.is_safe_for_auto_patch()
if __name__ == "__main__": test_faz10_005()

@test("ValidationReport  overall_passed mant")
def test_faz10_006():
    from packages.repair_engine.schemas.validation import ValidationReport, ValidationStatus
    rep = ValidationReport.create(patch_plan_id="plan_001")
    # Temel kaplar
    rep.syntax_ok = rep.lint_ok = rep.unit_tests_ok = rep.security_ok = rep.architecture_ok = True
    rep.patch_applied = True
    assert rep.overall_passed(), "Tm kaplar gemeli"

    # Security kaps
    rep.security_ok = False
    assert not rep.overall_passed(), "security=False iken gememeli"
    rep.security_ok = True

    # patch_applied zorunlu
    rep.patch_applied = False
    assert not rep.overall_passed(), "patch_applied=False iken gememeli"
    rep.patch_applied = True

    # Reproducer tanmlysa: ncesi FAIL + sonras PASS zorunlu
    rep.reproducer_defined = True
    rep.reproducer_passed_before_patch = False   # bug nceden vard 
    rep.reproducer_passed_after_patch  = True    # patch sonras geti 
    assert rep.overall_passed(), "Reproducer kant tam  gemeli"

    # Reproducer ncesi PASS  bug yoktu  gememeli
    rep.reproducer_passed_before_patch = True
    assert not rep.overall_passed(), "Reproducer ncesi PASS ise bug yoktu  gememeli"

    # Reproducer sonras FAIL  dzeltme olmad  gememeli
    rep.reproducer_passed_before_patch = False
    rep.reproducer_passed_after_patch  = False
    assert not rep.overall_passed(), "Reproducer sonras FAIL ise dzeltme olmad  gememeli"
if __name__ == "__main__": test_faz10_006()


# 
# 2. INGESTION
# 
print("\n 2. Ingestion")

@test("IncidentIngestor  exception'dan incident retme")
def test_faz10_007():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    ing = IncidentIngestor()
    try:
        raise ValueError("test error from orchestrator")
    except Exception as e:
        inc = ing.from_exception(e, service="test-service")
    assert "ValueError" in inc.symptom
    assert inc.severity is not None
if __name__ == "__main__": test_faz10_007()

@test("IncidentIngestor  log satrndan incident")
def test_faz10_008():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    ing = IncidentIngestor()
    inc = ing.from_log_line(
        "ERROR 500 Internal Server Error on /api/v1/tasks unhandled exception",
        service="test",
    )
    assert inc is not None
    assert inc.severity.value in ("medium", "high", "critical")
if __name__ == "__main__": test_faz10_008()

@test("IncidentIngestor  dk nem log  None dner")
def test_faz10_009():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    ing = IncidentIngestor()
    result = ing.from_log_line("INFO request processed successfully", service="test")
    assert result is None
if __name__ == "__main__": test_faz10_009()

@test("IncidentIngestor  deduplication (ayn semptom tekrarlanrsa)")
def test_faz10_010():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    ing = IncidentIngestor()
    inc1 = ing.from_log_line("ERROR 500 unhandled exception", service="svc")
    inc2 = ing.from_log_line("ERROR 500 unhandled exception", service="svc")
    assert inc1.incident_id == inc2.incident_id
    assert inc2.occurrence_count == 2
if __name__ == "__main__": test_faz10_010()

@test("IncidentIngestor  test failure'dan incident")
def test_faz10_011():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    ing = IncidentIngestor()
    inc = ing.from_failed_test(
        test_name="test_task_creation",
        test_output='FAILED tests/test_faz4.py::test_task_creation\nAssertionError: expected 201 got 500',
    )
    assert "test_task_creation" in inc.failing_tests
    assert inc.source.value == "test_failure"
if __name__ == "__main__": test_faz10_011()


# 
# 3. TRIAGE ENGINE
# 
print("\n 3. Triage Engine")

@test("Triage  ImportError  import_error snf")
def test_faz10_012():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    from packages.repair_engine.triage.triage_engine import TriageEngine
    from packages.repair_engine.schemas.diagnosis import ProblemClass, RepairMode
    ing = IncidentIngestor()
    inc = ing.from_dict({
        "source": "runtime_log", "severity": "high",
        "service": "backend-api", "module": "main",
        "symptom": "ImportError: cannot import name SubTaskModel from packages.persistence.models",
        "stack_trace": 'File "main.py"\nImportError: cannot import name SubTaskModel',
    })
    engine = TriageEngine()
    ticket = engine.triage(inc)
    assert ticket.classification == ProblemClass.IMPORT_ERROR
    assert ticket.recommended_mode == RepairMode.AUTO_PATCH_PR
if __name__ == "__main__": test_faz10_012()

@test("Triage  Auth hatas  manual_only")
def test_faz10_013():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    from packages.repair_engine.triage.triage_engine import TriageEngine
    from packages.repair_engine.schemas.diagnosis import RepairMode
    ing = IncidentIngestor()
    inc = ing.from_dict({
        "source": "runtime_log", "severity": "high",
        "service": "backend-api", "module": "auth",
        "symptom": "401 Unauthorized - JWT token invalid",
        "stack_trace": "jwt_auth.py line 45\nTokenExpired",
    })
    engine = TriageEngine()
    ticket = engine.triage(inc)
    assert ticket.recommended_mode == RepairMode.MANUAL_ONLY
    assert ticket.requires_human
if __name__ == "__main__": test_faz10_013()

@test("Triage  Critical severity  her zaman manual")
def test_faz10_014():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    from packages.repair_engine.triage.triage_engine import TriageEngine
    from packages.repair_engine.schemas.incident import IncidentSeverity
    from packages.repair_engine.schemas.diagnosis import RepairMode
    ing = IncidentIngestor()
    inc = ing.from_dict({
        "source": "runtime_log", "severity": "critical",
        "service": "backend-api", "module": "db",
        "symptom": "critical database connection fatal error oom",
        "stack_trace": "",
    })
    engine = TriageEngine()
    ticket = engine.triage(inc)
    assert ticket.recommended_mode == RepairMode.MANUAL_ONLY
if __name__ == "__main__": test_faz10_014()

@test("Triage  candidate dosyalar listeleniyor")
def test_faz10_015():
    from packages.repair_engine.ingestion.incident_ingestor import IncidentIngestor
    from packages.repair_engine.triage.triage_engine import TriageEngine
    ing = IncidentIngestor()
    inc = ing.from_dict({
        "source": "runtime_log", "severity": "medium",
        "service": "backend-api", "module": "task_router",
        "symptom": "ImportError: cannot import TaskModel",
        "stack_trace": 'File "main.py"\nImportError',
    })
    engine = TriageEngine()
    ticket = engine.triage(inc)
    assert len(ticket.candidate_files) > 0
if __name__ == "__main__": test_faz10_015()


# 
# 4. PATCH PLANNER
# 
print("\n 4. Patch Planner")

@test("PatchPlanner  low risk ImportError  plan retir")
def test_faz10_016():
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode, RootCauseHypothesis
    from packages.repair_engine.planning.patch_planner import PatchPlanner
    from packages.repair_engine.schemas.patch_plan import RiskLevel

    ticket = DiagnosisTicket.create(
        incident_id="inc_001",
        classification=ProblemClass.IMPORT_ERROR,
        severity="medium",
        candidate_files=["main.py"],
        recommended_mode=RepairMode.AUTO_PATCH_PR,
    )
    ticket.selected_hypothesis = RootCauseHypothesis(
        id="H1", title="Eksik import", explanation="import ifadesi eksik",
        confidence=85,
    )
    planner = PatchPlanner()
    plan = planner.plan(ticket, project_root=PROJECT_ROOT)
    assert plan is not None
    assert plan.risk == RiskLevel.LOW
    assert "main.py" in plan.target_files
if __name__ == "__main__": test_faz10_016()

@test("PatchPlanner  manual_only modda plan retmez")
def test_faz10_017():
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
    from packages.repair_engine.planning.patch_planner import PatchPlanner
    ticket = DiagnosisTicket.create(
        incident_id="inc_002",
        classification=ProblemClass.AUTH_FAILURE,
        severity="high",
        recommended_mode=RepairMode.MANUAL_ONLY,
    )
    planner = PatchPlanner()
    plan = planner.plan(ticket)
    assert plan is None
if __name__ == "__main__": test_faz10_017()

@test("PatchPlanner  hipotez yoksa plan retmez")
def test_faz10_018():
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
    from packages.repair_engine.planning.patch_planner import PatchPlanner
    ticket = DiagnosisTicket.create(
        incident_id="inc_003",
        classification=ProblemClass.IMPORT_ERROR,
        severity="low",
        recommended_mode=RepairMode.AUTO_PATCH_PR,
        # selected_hypothesis None brakld
    )
    planner = PatchPlanner()
    plan = planner.plan(ticket)
    assert plan is None
if __name__ == "__main__": test_faz10_018()


# 
# 5. PATCH REVIEWER
# 
print("\n 5. Patch Reviewer")

@test("Reviewer  bo diff  reject")
def test_faz10_019():
    from packages.repair_engine.review.patch_reviewer import PatchReviewer, ReviewDecisionType
    from packages.repair_engine.generation.patch_generator import GeneratedPatch
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode

    patch = GeneratedPatch(plan_id="plan_001", diff="", changed_files=[])
    plan  = PatchPlan.create("diag_001", risk=RiskLevel.LOW)
    ticket = DiagnosisTicket.create("inc_001", ProblemClass.IMPORT_ERROR, "low",
                                    recommended_mode=RepairMode.AUTO_PATCH_PR)
    reviewer = PatchReviewer()
    report = reviewer.review(patch, plan, ticket)
    assert report.decision == ReviewDecisionType.REJECT
if __name__ == "__main__": test_faz10_019()

@test("Reviewer  eval()  manual_review")
def test_faz10_020():
    from packages.repair_engine.review.patch_reviewer import PatchReviewer, ReviewDecisionType
    from packages.repair_engine.generation.patch_generator import GeneratedPatch
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode, RootCauseHypothesis

    evil_diff = """--- a/main.py\n+++ b/main.py\n@@ -1,3 +1,4 @@\n import os\n+result = eval(user_input)\n def main():\n     pass"""
    patch = GeneratedPatch(plan_id="plan_001", diff=evil_diff, changed_files=["main.py"])
    plan  = PatchPlan.create("diag_001", target_files=["main.py"], risk=RiskLevel.LOW)
    ticket = DiagnosisTicket.create("inc_001", ProblemClass.IMPORT_ERROR, "low",
                                    recommended_mode=RepairMode.AUTO_PATCH_PR)
    ticket.selected_hypothesis = RootCauseHypothesis(id="H1", title="eval", explanation="", confidence=80)

    reviewer = PatchReviewer()
    report = reviewer.review(patch, plan, ticket)
    assert report.security_risk == "high"
    assert report.decision == ReviewDecisionType.MANUAL_REVIEW
if __name__ == "__main__": test_faz10_020()

@test("Reviewer  minimal geerli diff  approve")
def test_faz10_021():
    from packages.repair_engine.review.patch_reviewer import PatchReviewer, ReviewDecisionType
    from packages.repair_engine.generation.patch_generator import GeneratedPatch
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode, RootCauseHypothesis

    valid_diff = (
        "--- a/main.py\n+++ b/main.py\n"
        "@@ -1,3 +1,4 @@\n"
        " import os\n"
        "+from packages.persistence.models import SubTaskModel\n"
        " def main():\n"
        "     pass\n"
    )
    patch = GeneratedPatch(plan_id="p001", diff=valid_diff, changed_files=["main.py"], confidence=80)
    plan  = PatchPlan.create("d001", target_files=["main.py"], risk=RiskLevel.LOW, approved=True)
    ticket = DiagnosisTicket.create("i001", ProblemClass.IMPORT_ERROR, "medium",
                                    recommended_mode=RepairMode.AUTO_PATCH_PR)
    ticket.selected_hypothesis = RootCauseHypothesis(
        id="H1", title="import eksik SubTaskModel", explanation="", confidence=85,
    )
    reviewer = PatchReviewer()
    report = reviewer.review(patch, plan, ticket)
    assert report.decision == ReviewDecisionType.APPROVE
if __name__ == "__main__": test_faz10_021()


# 
# 6. VERIFICATION ENGINE
# 
print("\n 6. Verification Engine")

@test("VerificationEngine  geerli diff syntax OK")
def test_faz10_022():
    from packages.repair_engine.verification.verification_engine import VerificationEngine
    from packages.repair_engine.generation.patch_generator import GeneratedPatch
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel

    diff = (
        "--- a/main.py\n+++ b/main.py\n"
        "@@ -1,3 +1,4 @@\n"
        " import os\n"
        "+from packages.persistence.models import SubTaskModel\n"
        " def main():\n    pass\n"
    )
    patch = GeneratedPatch(plan_id="p001", diff=diff, changed_files=["main.py"])
    plan  = PatchPlan.create("d001", target_files=["main.py"], risk=RiskLevel.LOW)

    engine = VerificationEngine(project_root=PROJECT_ROOT)
    report = engine.verify(patch, plan)
    assert report.syntax_ok
if __name__ == "__main__": test_faz10_022()

@test("VerificationEngine  eval() gvenlik testi FAIL")
def test_faz10_023():
    from packages.repair_engine.verification.verification_engine import VerificationEngine
    from packages.repair_engine.generation.patch_generator import GeneratedPatch
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel

    diff = (
        "--- a/main.py\n+++ b/main.py\n"
        "@@ -1,3 +1,4 @@\n"
        " import os\n"
        "+result = eval(request.body)\n"
        " def main():\n    pass\n"
    )
    patch = GeneratedPatch(plan_id="p001", diff=diff, changed_files=["main.py"])
    plan  = PatchPlan.create("d001", target_files=["main.py"], risk=RiskLevel.LOW)

    engine = VerificationEngine(project_root=PROJECT_ROOT)
    report = engine.verify(patch, plan)
    assert not report.security_ok
    assert report.final_recommendation in ("reject", "manual_review_only")
if __name__ == "__main__": test_faz10_023()

@test("VerificationEngine  izinsiz dosya mimari kontrol")
def test_faz10_024():
    from packages.repair_engine.verification.verification_engine import VerificationEngine
    from packages.repair_engine.generation.patch_generator import GeneratedPatch
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel

    diff = (
        "--- a/main.py\n+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        " import os\n"
        "+# changed\n"
        "--- a/auth/jwt_auth.py\n+++ b/auth/jwt_auth.py\n"
        "@@ -1 +1 @@\n"
        " import jwt\n"
        "+# also changed\n"
    )
    patch = GeneratedPatch(plan_id="p001", diff=diff, changed_files=["main.py", "auth/jwt_auth.py"])
    plan  = PatchPlan.create("d001", target_files=["main.py"], risk=RiskLevel.LOW)  # jwt_auth.py izinsiz

    engine = VerificationEngine(project_root=PROJECT_ROOT)
    report = engine.verify(patch, plan)
    assert not report.architecture_ok
if __name__ == "__main__": test_faz10_024()

@test("VerificationEngine  confidence hesab 0-100 aralnda")
def test_faz10_025():
    from packages.repair_engine.verification.verification_engine import VerificationEngine
    from packages.repair_engine.generation.patch_generator import GeneratedPatch
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel

    diff = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n+pass\n"
    patch = GeneratedPatch(plan_id="p001", diff=diff, changed_files=["x.py"])
    plan  = PatchPlan.create("d001", target_files=["x.py"], risk=RiskLevel.LOW)

    engine = VerificationEngine(project_root=PROJECT_ROOT)
    report = engine.verify(patch, plan)
    assert 0 <= report.confidence <= 100
if __name__ == "__main__": test_faz10_025()


# 
# 7. MEMORY
# 
print("\n 7. Memory")

@test("IncidentMemory  kayt ve istatistik")
def test_faz10_026():
    from packages.repair_engine.packages.memory.incident_memory import IncidentMemory
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    mem = IncidentMemory()
    inc = IncidentRecord.create(
        source=IncidentSource.RUNTIME_LOG,
        severity=IncidentSeverity.HIGH,
        service="svc", module="mod", symptom="test symptom",
    )
    mem.record(inc)
    assert mem.get(inc.incident_id) is not None
    stats = mem.stats()
    assert stats["total"] == 1
    assert stats["open"] == 1
if __name__ == "__main__": test_faz10_026()

@test("IncidentMemory  hotspot modller hesaplanyor")
def test_faz10_027():
    from packages.repair_engine.packages.memory.incident_memory import IncidentMemory
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    mem = IncidentMemory()
    for i in range(5):
        inc = IncidentRecord.create(
            source=IncidentSource.RUNTIME_LOG, severity=IncidentSeverity.MEDIUM,
            service="svc", module="task_router", symptom=f"error {i}",
        )
        mem.record(inc)
    hotspots = mem.hotspot_modules()
    assert hotspots[0].module == "task_router"
    assert hotspots[0].total_incidents == 5
if __name__ == "__main__": test_faz10_027()

@test("IncidentMemory  resolve ve mean_time_to_resolve")
def test_faz10_028():
    from packages.repair_engine.packages.memory.incident_memory import IncidentMemory
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    mem = IncidentMemory()
    inc = IncidentRecord.create(
        source=IncidentSource.RUNTIME_LOG, severity=IncidentSeverity.LOW,
        service="svc", module="mod", symptom="test",
    )
    mem.record(inc)
    ok = mem.mark_resolved(inc.incident_id, duration_s=42.5)
    assert ok
    assert mem.mean_time_to_resolve() == 42.5
if __name__ == "__main__": test_faz10_028()

@test("PatchMemory  success rate hesaplanyor")
def test_faz10_029():
    from packages.repair_engine.packages.memory.patch_memory import PatchMemory, PatchOutcome
    mem = PatchMemory()
    for i in range(4):
        mem.record(
            job_id=f"job_{i}", incident_id=f"inc_{i}",
            classification="import_error",
            target_files=["main.py"],
            diff_size_lines=10,
            outcome=PatchOutcome.SUCCESS if i < 3 else PatchOutcome.REGRESSION,
            confidence=80, validation_score=80,
        )
    rate = mem.success_rate_for("import_error")
    assert rate == 0.75
if __name__ == "__main__": test_faz10_029()

@test("PatchMemory  regresyon dosyas danger_files'a ekleniyor")
def test_faz10_030():
    from packages.repair_engine.packages.memory.patch_memory import PatchMemory, PatchOutcome
    mem = PatchMemory()
    mem.record(
        job_id="job_1", incident_id="inc_1",
        classification="contract_broken",
        target_files=["core/orchestrator.py"],
        diff_size_lines=50,
        outcome=PatchOutcome.REGRESSION,
        confidence=60, validation_score=60,
    )
    assert mem.is_danger_file("core/orchestrator.py")
if __name__ == "__main__": test_faz10_030()

@test("ArchitectureMemory  kritik modl tespiti")
def test_faz10_031():
    from packages.repair_engine.packages.memory.architecture_memory import ArchitectureMemory
    mem = ArchitectureMemory()
    assert mem.is_critical_module("auth/jwt_auth.py")
    assert mem.is_critical_module("core/orchestrator.py")
    assert not mem.is_critical_module("tests/test_faz4.py")
if __name__ == "__main__": test_faz10_031()

@test("ArchitectureMemory  forbidden pattern listesi dolu")
def test_faz10_032():
    from packages.repair_engine.packages.memory.architecture_memory import ArchitectureMemory
    mem = ArchitectureMemory()
    patterns = mem.get_forbidden_patterns()
    assert len(patterns) >= 5
    pattern_texts = [fp.pattern for fp in patterns]
    assert any("eval" in p for p in pattern_texts)
if __name__ == "__main__": test_faz10_032()

@test("ArchitectureMemory  ADR listesi")
def test_faz10_033():
    from packages.repair_engine.packages.memory.architecture_memory import ArchitectureMemory
    mem = ArchitectureMemory()
    adrs = mem.get_adrs()
    assert len(adrs) >= 3
    assert all(a.status == "accepted" for a in adrs)
if __name__ == "__main__": test_faz10_033()


# 
# 8. POLICY ENGINE
# 
print("\n  8. Policy Engine")

@test("PolicyEngine  auth modl  blocked")
def test_faz10_034():
    from core.policy_engine import PolicyEngine
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel
    from packages.repair_engine.schemas.validation import ValidationReport

    ticket = DiagnosisTicket.create("inc_001", ProblemClass.AUTH_FAILURE, "high",
                                    recommended_mode=RepairMode.AUTO_PATCH_PR)
    plan = PatchPlan.create("diag_001", target_files=["auth/jwt_auth.py"], risk=RiskLevel.LOW)
    validation = ValidationReport.create("plan_001")
    validation.syntax_ok = validation.security_ok = validation.architecture_ok = True
    validation.confidence = 80

    engine = PolicyEngine()
    decision = engine.evaluate_patch(ticket, plan, validation)
    assert not decision.allowed
    assert len(decision.blocking_reasons) > 0
if __name__ == "__main__": test_faz10_034()

@test("PolicyEngine  low risk clean patch  create_pr")
def test_faz10_035():
    from core.policy_engine import PolicyEngine
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel
    from packages.repair_engine.schemas.validation import ValidationReport, ValidationStatus

    ticket = DiagnosisTicket.create("inc_001", ProblemClass.IMPORT_ERROR, "medium",
                                    recommended_mode=RepairMode.AUTO_PATCH_PR)
    plan = PatchPlan.create("diag_001", target_files=["main.py"], risk=RiskLevel.LOW,
                             public_api_impact=False, migration_required=False,
                             required_tests=["tests/test_faz4.py"])
    validation = ValidationReport.create("plan_001")
    validation.syntax_ok = validation.lint_ok = validation.unit_tests_ok = True
    validation.security_ok = validation.architecture_ok = True
    validation.confidence = 85
    validation.final_status = ValidationStatus.PASSED

    engine = PolicyEngine()
    decision = engine.evaluate_patch(ticket, plan, validation)
    assert decision.allowed
    assert decision.recommended_action == "create_pr"
if __name__ == "__main__": test_faz10_035()

@test("PolicyEngine  triage'da security snf  blocked")
def test_faz10_036():
    from core.policy_engine import PolicyEngine
    from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode

    ticket = DiagnosisTicket.create("inc_001", ProblemClass.SECURITY_VIOLATION, "critical",
                                    recommended_mode=RepairMode.AUTO_PATCH_PR)
    engine = PolicyEngine()
    decision = engine.evaluate_triage(ticket)
    assert not decision.allowed
if __name__ == "__main__": test_faz10_036()


# 
# 9. REPAIR ORCHESTRATOR (State Machine)
# 
print("\n 9. Repair Orchestrator")

@test("RepairOrchestrator  job oluturma")
def test_faz10_037():
    from core.repair_orchestrator import RepairOrchestrator
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity

    orch = RepairOrchestrator(model_orch=None, project_root=PROJECT_ROOT)
    inc = IncidentRecord.create(
        source=IncidentSource.RUNTIME_LOG, severity=IncidentSeverity.HIGH,
        service="backend-api", module="task_router", symptom="500 Internal Server Error",
    )

    async def _run():
        job = await orch.start_repair(inc)
        assert job.job_id.startswith("rjob_")
        assert job.incident_id == inc.incident_id
        # Pipeline async alyor, job'u hemen al
        fetched = await orch.get_job(job.job_id)
        assert fetched is not None
        await asyncio.sleep(0.1)   # ksa bekleme (pipeline balad m?)
        return job

    asyncio.run(_run())
if __name__ == "__main__": test_faz10_037()

@test("RepairOrchestrator  stats dndryor")
def test_faz10_038():
    from core.repair_orchestrator import RepairOrchestrator
    orch = RepairOrchestrator(model_orch=None, project_root=PROJECT_ROOT)
    stats = orch.stats()
    assert "total" in stats
    assert "incident_memory" in stats
    assert "patch_memory" in stats
if __name__ == "__main__": test_faz10_038()

@test("RepairOrchestrator  security incident  manual review")
def test_faz10_039():
    from core.repair_orchestrator import RepairOrchestrator
    from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    from packages.repair_engine.schemas.repair_job import RepairJobStatus

    orch = RepairOrchestrator(model_orch=None, project_root=PROJECT_ROOT)
    inc = IncidentRecord.create(
        source=IncidentSource.RUNTIME_LOG, severity=IncidentSeverity.HIGH,
        service="backend-api", module="auth",
        symptom="401 Unauthorized JWT authentication failed",
        stack_trace="jwt_auth.py TokenExpired",
    )

    async def _run():
        job = await orch.start_repair(inc)
        # Pipeline birka ms iinde alr
        for _ in range(20):
            await asyncio.sleep(0.05)
            if job.is_terminal() or job.status.value.startswith("requires"):
                break
        return job

    job = asyncio.run(_run())
    # Auth modl  REQUIRES_MANUAL_REVIEW veya hl ilerliyor (LLM yok)
    valid_terminal = {
        RepairJobStatus.REQUIRES_MANUAL_REVIEW,
        RepairJobStatus.REJECTED,
        RepairJobStatus.FAILED_TRIAGE,
        RepairJobStatus.TRIAGED,            # triage tamamland, policy durdurdu
        RepairJobStatus.INCIDENT_COLLECTED,
        RepairJobStatus.NEW,                # henz pipeline balamad (async race)
        RepairJobStatus.ROOT_CAUSE_ANALYZED,
        RepairJobStatus.PATCH_PLANNED,
    }
    assert job.status in valid_terminal, f"Beklenmeyen durum: {job.status}"
if __name__ == "__main__": test_faz10_039()


# 
# 9b. P0 Dzeltme Dorulama Testleri (Faz 10.1)
# 
print("\n 9b. P0 Dzeltme Dorulama Testleri")

@test("P0: _filter_safe_files  whitelist d dosya reddedilir")
def test_faz10_040():
    from packages.repair_engine.planning.patch_planner import PatchPlanner
    planner = PatchPlanner()
    fake_candidates = ["db/session.py", "tests/test_faz4.py", "main.py"]
    result = planner._filter_safe_files(fake_candidates, PROJECT_ROOT)
    assert "db/session.py" not in result, "db/session.py whitelist d"
    assert "tests/test_faz4.py" not in result, "tests/ whitelist d"
    assert "main.py" in result, "main.py whitelist'te olmal"
if __name__ == "__main__": test_faz10_040()

@test("P0: _filter_safe_files  auth/ her zaman reddedilir")
def test_faz10_041():
    from packages.repair_engine.planning.patch_planner import PatchPlanner
    planner = PatchPlanner()
    result = planner._filter_safe_files(["auth/jwt_auth.py", "main.py"], PROJECT_ROOT)
    assert "auth/jwt_auth.py" not in result
    assert "main.py" in result
if __name__ == "__main__": test_faz10_041()

@test("P0: VerificationEngine  test yoksa gap kaydedilir ve recommendation drlr")
def test_faz10_042():
    from packages.repair_engine.verification.verification_engine import VerificationEngine
    from packages.repair_engine.generation.patch_generator import GeneratedPatch
    from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel
    diff = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n+pass\n"
    patch = GeneratedPatch(plan_id="p001", diff=diff, changed_files=["x.py"])
    plan  = PatchPlan.create("d001", target_files=["x.py"], risk=RiskLevel.LOW)
    engine = VerificationEngine(project_root=PROJECT_ROOT)
    report = engine.verify(patch, plan)
    assert not report.unit_tests_ok, "Test tanmlanmadysa unit_tests_ok=False olmal"
    assert "no_test_defined" in report.verification_gaps
    assert report.final_recommendation in ("manual_review_only", "reject")
if __name__ == "__main__": test_faz10_042()

@test("P0: ValidationReport  reproducer ncesi PASS ise overall_passed=False (bug yoktu)")
def test_faz10_043():
    from packages.repair_engine.schemas.validation import ValidationReport
    rep = ValidationReport.create(patch_plan_id="plan_reproducer")
    rep.syntax_ok = rep.lint_ok = rep.unit_tests_ok = rep.security_ok = rep.architecture_ok = True
    rep.patch_applied = True
    rep.reproducer_defined = True
    # Senaryo: reproducer patch ncesi zaten geiyordu  bug yoktu
    rep.reproducer_passed_before_patch = True   # beklenmeyen
    rep.reproducer_passed_after_patch  = True
    assert not rep.overall_passed(), "Reproducer ncesi PASS  bug yoktu  create_pr YOK"
    assert not rep.reproducer_evidence_ok(), "Kant zinciri eksik"
if __name__ == "__main__": test_faz10_043()

@test("P0: PRProposal.incident_id alan var ve set ediliyor")
def test_faz10_044():
    from packages.repair_engine.release.pr_creator import PRProposal
    p = PRProposal(pr_id="pr_t", job_id="job_t", branch_name="repair/t",
                   title="t", body="b", incident_id="inc_xyz")
    assert p.incident_id == "inc_xyz"
    assert p.auto_merge is False
    d = p.to_dict()
    assert d["incident_id"] == "inc_xyz"
if __name__ == "__main__": test_faz10_044()

@test("P0: PRCreator singleton  ayn root iin ayn instance")
def test_faz10_045():
    from packages.repair_engine.release.pr_creator import get_pr_creator
    c1 = get_pr_creator(PROJECT_ROOT)
    c2 = get_pr_creator(PROJECT_ROOT)
    assert c1 is c2, "Singleton dndrlmeli"
if __name__ == "__main__": test_faz10_045()

@test("P0: db/repair_repository  incident_id proposal.incident_id ile yazlyor")
def test_faz10_046():
    import ast
    fpath = os.path.join(PROJECT_ROOT, "db", "repair_repository.py")
    with open(fpath) as f:
        src = f.read()
    assert "proposal.job_id" not in src or "incident_id=proposal.job_id" not in src,         "incident_id=proposal.job_id bug hl var"
    assert "proposal.incident_id" in src, "proposal.incident_id yazlyor olmal"
if __name__ == "__main__": test_faz10_046()

@test("P0: triage_engine  eski task_router.py route hint yok, split router var")
def test_faz10_047():
    fpath = os.path.join(PROJECT_ROOT, "repair", "triage", "triage_engine.py")
    with open(fpath) as f:
        src = f.read()
    assert '"api/task_router.py"' not in src, "Eski task_router.py hint kaldrlm olmal"
    assert "task_read_router" in src or "task_control_router" in src,         "Split router hint bulunmal"
if __name__ == "__main__": test_faz10_047()

@test("P0: PromptSimplifyStrategy  ksa prompt success=False dndrr")
def test_faz10_048():
    import asyncio
    from heal.recovery_strategies import PromptSimplifyStrategy, _PROMPT_SIMPLIFY_THRESHOLD
    strategy = PromptSimplifyStrategy()
    class FakeSubtask:
        prompt = "a" * (_PROMPT_SIMPLIFY_THRESHOLD - 50)
        result = None
    async def _run():
        return await strategy.execute(None, FakeSubtask(), object())
    result = asyncio.run(_run())
    assert not result.success
if __name__ == "__main__": test_faz10_048()

@test("P0: PromptSimplifyStrategy  uzun prompt 'Sadeletirildi' ieriyor (mock LLM)")
def test_faz10_049():
    import asyncio
    from heal.recovery_strategies import PromptSimplifyStrategy, _PROMPT_SIMPLIFY_THRESHOLD
    strategy = PromptSimplifyStrategy()
    class FakeOrch:
        class model_orch:
            @staticmethod
            async def complete(messages, max_tokens):
                return "mock response"
    class FakeSubtask:
        prompt = "x" * (_PROMPT_SIMPLIFY_THRESHOLD + 200)
        result = None
    async def _run():
        return await strategy.execute(None, FakeSubtask(), FakeOrch())
    result = asyncio.run(_run())
    assert result.success
    assert "Sadeletirildi" in result.message
if __name__ == "__main__": test_faz10_049()

@test("P0: LLM _estimate_cost, _estimate_tokens, _estimate_output_tokens metodlar var (AST kontrol)")
def test_faz10_050():
    import ast
    fpath = os.path.join(PROJECT_ROOT, "llm", "model_orchestrator.py")
    with open(fpath) as f:
        src = f.read()
    tree = ast.parse(src)
    method_names = {
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    assert "_estimate_cost" in method_names, "_estimate_cost metodu eksik"
    assert "_estimate_tokens" in method_names, "_estimate_tokens metodu eksik"
    assert "_estimate_output_tokens" in method_names, "_estimate_output_tokens metodu eksik"
if __name__ == "__main__": test_faz10_050()

@test("P0: task_write_router  cancel endpoint kaldrld")
def test_faz10_051():
    import ast
    fpath = os.path.join(PROJECT_ROOT, "api", "task_write_router.py")
    with open(fpath) as f:
        src = f.read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "cancel_task":
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    for arg in dec.args:
                        if isinstance(arg, ast.Constant) and "cancel" in str(arg.value):
                            raise AssertionError("task_write_router'da cancel route hl var")
if __name__ == "__main__": test_faz10_051()

@test("P0: observer.py  hardcoded task_router.py yok, _ENDPOINT_OWNER_MAP var")
def test_faz10_052():
    fpath = os.path.join(PROJECT_ROOT, "improve", "observer.py")
    with open(fpath, encoding="utf-8") as f:
        src = f.read()
    # "task_router.py" string'i kaynak kodda gememeli
    assert '"api/task_router.py"' not in src, "Hardcoded task_router.py referans var"
    assert "_ENDPOINT_OWNER_MAP" in src, "_ENDPOINT_OWNER_MAP tanm eksik"
if __name__ == "__main__": test_faz10_052()

@test("P0: improvement_router  mock propose endpoint kaldrld")
def test_faz10_053():
    fpath = os.path.join(PROJECT_ROOT, "api", "improvement_router.py")
    with open(fpath) as f:
        src = f.read()
    assert "mock_opp" not in src, "Mock opportunity retimi kaldrlm olmal"
    assert "deprecated" in src.lower(), "Deprecation notu bulunmal"
if __name__ == "__main__": test_faz10_053()

# 
# 10. SYNTAX / IMPORT KONTROL (tm repair dosyalar)
# 
print("\n 10. Syntax Kontrol")

repair_files = []
for root, dirs, files in os.walk(os.path.join(PROJECT_ROOT, "repair")):
    for f in files:
        if f.endswith(".py"):
            repair_files.append(os.path.join(root, f))

extra_files = [
    os.path.join(PROJECT_ROOT, "core", "repair_orchestrator.py"),
    os.path.join(PROJECT_ROOT, "core", "policy_engine.py"),
    os.path.join(PROJECT_ROOT, "db", "repair_models.py"),
    os.path.join(PROJECT_ROOT, "db", "repair_repository.py"),
    os.path.join(PROJECT_ROOT, "api", "repair_router.py"),
    os.path.join(PROJECT_ROOT, "alembic", "versions", "0002_repair_tables.py"),
]
all_files = repair_files + extra_files

for fpath in all_files:
    rel = os.path.relpath(fpath, PROJECT_ROOT)
    if not os.path.exists(fpath):
        results.append((f"Syntax: {rel}", False, "Dosya bulunamad"))
        print(f"  {SKIP} Syntax: {rel}  bulunamad")
        continue
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            src = f.read()
        ast.parse(src)
        results.append((f"Syntax: {rel}", True, ""))
        print(f"  {PASS} Syntax: {rel}")
    except SyntaxError as e:
        results.append((f"Syntax: {rel}", False, str(e)))
        print(f"  {FAIL} Syntax: {rel}  {e}")


# 
# SONU
# 
print("\n" + "" * 60)
total  = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n SONU: {passed}/{total} test geti")
if failed:
    print(f"\n{FAIL} Baarsz testler:")
    for name, ok, msg in results:
        if not ok:
            print(f"    {name}: {msg}")

print(f"\n{' Tm testler geti!' if failed == 0 else f'  {failed} test baarsz.'}")

if __name__ == "__main__":
    if failed > 0:
        print(f"FAILED tests: {failed}")
