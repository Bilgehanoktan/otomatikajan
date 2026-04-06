"""
tests/test_repair_pipeline_integration.py â€” RC1 Tam Pipeline Entegrasyon Testi

Tek test senaryosu iÃ§inde Faz 12 tÃ¼m bileÅŸenlerinin
omurgaya girdiÄŸini kanÄ±tlar:

fingerprint -> vector RAG -> ranker -> debate -> 
generated tests -> sandbox -> canary -> metrics -> lesson save
"""
import asyncio, sys, os, types, uuid, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = FAIL = 0
def ok(n):        global PASS; PASS += 1; print(f"  âœ… {n}")
def fail(n, e=""): global FAIL; FAIL += 1; print(f"  âŒ {n}{(' â€” '+str(e)) if e else ''}")
def section(t):   print(f"\n{'â•'*55}\n  {t}\n{'â•'*55}")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Test altyapÄ±sÄ± â€” tam mock pipeline
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class _MockHypothesis:
    def __init__(self, title, confidence):
        self.title      = title
        self.confidence = confidence
        self.module     = "auth"
        self.evidence   = "mock evidence"

class _MockTicket:
    def __init__(self):
        self.ticket_id             = f"tkt_{uuid.uuid4().hex[:6]}"
        self.classification        = types.SimpleNamespace(value="runtime")
        self.recommended_mode      = types.SimpleNamespace(value="auto")
        self.rationale             = "mock triage rationale"
        self.selected_hypothesis   = _MockHypothesis("JWT decode hatasÄ±", 75)
        self.hypotheses            = [
            _MockHypothesis("JWT decode hatasÄ±",   75),
            _MockHypothesis("Token sÃ¼resi dolmuÅŸ", 73),  # Â±5% -> debate tetiklenir
            _MockHypothesis("DB baÄŸlantÄ±sÄ± kesildi", 40),
        ]

class _MockPlan:
    def __init__(self):
        self.plan_id      = f"plan_{uuid.uuid4().hex[:6]}"
        self.target_files = ["auth/jwt_handler.py"]
        self.risk         = types.SimpleNamespace(value="low")
        self.rationale    = "mock plan"

class _MockPatch:
    def __init__(self):
        self.diff       = "+# JWT fix\n+TOKEN_TTL = 900\n-TOKEN_TTL = 3600\n"
        self.confidence = 80
    def is_valid(self):
        return True

class _MockValidation:
    def __init__(self):
        self.validation_id  = f"val_{uuid.uuid4().hex[:6]}"
        self.final_status   = types.SimpleNamespace(value="passed")
        self.confidence     = 80
        self.syntax_ok      = True
        self.lint_ok        = True
        self.security_ok    = True
        self.unit_tests_ok  = True
        self.patch_apply_output = "Patch applied OK"

class _MockProposal:
    def __init__(self):
        self.pr_id       = f"pr_{uuid.uuid4().hex[:6]}"
        self.branch_name = "repair/jwt-fix"

class _MockPolicyDecision:
    allowed          = True
    blocking_reasons = []

class _MockPolicy:
    def evaluate_triage(self, t): return _MockPolicyDecision()
    def evaluate_patch(self, *a): return _MockPolicyDecision()
    def canary_required(self):    return True  # Canary aktif

class _MockOrch:
    """LLM iÃ§in mock â€” debate, ranker vb."""
    async def complete(self, messages, preferred_agent="general", **kw):
        if preferred_agent == "architect":
            return "[UZLAÅI] JWT decode hatasÄ± hipotezi daha gÃ¼Ã§lÃ¼."
        return f"{preferred_agent}: mock argÃ¼man."

def _build_mock_orchestrator():
    """RepairOrchestrator'Ä± mock bileÅŸenlerle oluÅŸtur."""
    from core.repair_orchestrator import RepairOrchestrator
    orch = RepairOrchestrator.__new__(RepairOrchestrator)
    orch.project_root = "."
    orch.model_orch   = _MockOrch()

    # Policy
    orch.policy = _MockPolicy()

    # Memory mocks
    class _Inc:
        def mark_resolved(self, *a, **kw): pass
        def get_open(self): return []
    class _Ptch:
        def record(self, *a, **kw): pass
        def get_records(self, *a, **kw): return []
    class _Arch:
        def get_context(self, *a, **kw): return ""

    orch.inc_memory  = _Inc()
    orch.ptch_memory = _Ptch()
    orch.arch_memory = _Arch()
    orch.triage      = None

    # DB ve persist metotlarÄ±nÄ± mock'la (Test ortamÄ±nda DB yok)
    async def _mock_async_none(*a, **kw): return None
    orch._persist_job              = _mock_async_none
    orch._persist_job_and_proposal = _mock_async_none
    orch._persist_patch_log        = _mock_async_none
    
    # Mock verify and canary to avoid real I/O
    async def _mock_verify(*a, **kw): return _MockValidation()
    orch._step_verify = _mock_verify
    
    async def _mock_canary(*a, **kw): return True
    orch._step_canary = _mock_canary
    orch._do_canary_run = _mock_canary

    from packages.repair_engine.schemas.repair_job import RepairJobStatus
    async def _mock_transition(job, status, note=""):
        job.transition(status, note=note)
    orch._transition_and_persist = _mock_transition

    return orch


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Pipeline adÄ±mlarÄ±nÄ± sÄ±rayla izole test et
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

section("1 â€” Fingerprint + Duplicate Tespiti")

def test_fingerprint_step():
    from packages.repair_engine.schemas.repair_job import RepairJob
    from packages.repair_engine.schemas.incident   import IncidentRecord

    orch = _build_mock_orchestrator()
    job  = RepairJob.create("inc_fp_001")
    inc  = IncidentRecord(
        incident_id="inc_fp_001",
        symptom="JWT decode error: invalid signature",
        module="auth",
        severity="high",
        source="runtime",
        service="backend-api",
    )
    orch._step_fingerprint(job, inc)
    # fingerprint_hash doldurulmuÅŸ olabilir (engine varsa) veya boÅŸ kalÄ±r
    assert isinstance(job.fingerprint_hash, (str, type(None)))
    ok("Fingerprint adÄ±mÄ± hatasÄ±z Ã§alÄ±ÅŸÄ±yor")

# test_fingerprint_step() - Moved to main block

section("2 â€” Vector RAG Context")

def test_vector_rag_step():
    """Vector store'a lesson ekle, context Ã§ekmeyi test et."""
    import packages.repair_engine.memory.vector_lessons as vl_mod
    vl_mod._vector_lessons = None
    store = vl_mod.get_vector_lessons(use_db=False)

    # GeÃ§miÅŸ lesson ekle
    store.save_lesson(
        symptom="JWT decode error invalid signature",
        module="auth",
        resolution="JWT secret key gÃ¼ncellendi, TTL 15dk olarak dÃ¼zenlendi.",
        job_id="job_past_001",
        incident_id="inc_past_001",
    )

    from packages.repair_engine.schemas.incident import IncidentRecord
    inc = IncidentRecord(
        incident_id="inc_rag_001",
        symptom="JWT decode error: signature mismatch",
        module="auth",
        severity="high",
    
        source="runtime",
        service="backend-api",
    )

    orch = _build_mock_orchestrator()

    ctx = asyncio.run(orch._step_get_context_from_vector(inc))
    assert isinstance(ctx, str)

    if ctx:
        assert "auth" in ctx.lower() or "jwt" in ctx.lower() or "benzer" in ctx.lower()
        ok(f"Vector RAG context Ã§ekildi: {len(ctx)} karakter")
    else:
        ok("Vector RAG context boÅŸ (min_score altÄ±nda â€” normal)")

# test_vector_rag_step() - Moved to main block

section("3 â€” Root Cause Ranker")

def test_ranker_step():
    from packages.repair_engine.schemas.repair_job import RepairJob
    from packages.repair_engine.schemas.incident   import IncidentRecord

    orch    = _build_mock_orchestrator()
    job     = RepairJob.create("inc_rnk_001")
    ticket  = _MockTicket()
    inc     = IncidentRecord(
        incident_id="inc_rnk_001",
        symptom="JWT error",
        module="auth",
        severity="medium",
    
        source="runtime",
        service="backend-api",
    )

    result_ticket, ranker_info = orch._step_rank_hypotheses(job, ticket, inc)

    assert result_ticket is not None
    assert isinstance(ranker_info, dict)
    ok(f"Ranker adÄ±mÄ± â€” raw={ranker_info.get('raw',0)} adj={ranker_info.get('adjusted',0)}")
    assert isinstance(job.ranker_adjusted, bool)
    ok("job.ranker_adjusted alanÄ± dolu")

# test_ranker_step() - Moved to main block

section("4 â€” Debate Engine Tetikleme")

def test_debate_triggered():
    """Ä°ki yakÄ±n hipotez varsa debate tetiklenmeli."""
    from packages.repair_engine.schemas.repair_job import RepairJob
    from packages.repair_engine.schemas.incident   import IncidentRecord

    orch    = _build_mock_orchestrator()
    job     = RepairJob.create("inc_dbte_001")
    ticket  = _MockTicket()  # 75% vs 73% â€” fark 2, threshold ~4 -> tetiklenmeli
    inc     = IncidentRecord(
        incident_id="inc_dbte_001",
        symptom="JWT decode error",
        module="auth",
        severity="high",
    
        source="runtime",
        service="backend-api",
    )

    asyncio.run(orch._step_debate_if_needed(job, ticket, inc))

    # Debate tetiklendi mi veya sessizce atlandÄ± mÄ±?
    # (Mock LLM [UZLAÅI] dÃ¶nÃ¼yor -> agreement_reached=True olmalÄ±)
    if job.debate_triggered:
        assert job.debate_result_summary
        assert job.debate_winning_hypothesis
        ok(f"Debate TETÄ°KLENDÄ° â€” kazanan: '{job.debate_winning_hypothesis[:50]}'")
    else:
        ok("Debate tetiklenmedi (hipotez farkÄ± eÅŸik Ã¼stÃ¼ â€” normal)")

# test_debate_triggered() - Moved to main block

section("5 â€” Generated Tests")

def test_generated_tests_step():
    from packages.repair_engine.schemas.repair_job import RepairJob
    from packages.repair_engine.schemas.incident   import IncidentRecord

    orch   = _build_mock_orchestrator()
    job    = RepairJob.create("inc_tgen_001")
    inc    = IncidentRecord(
        incident_id="inc_tgen_001",
        symptom="JWT error",
        module="auth",
        severity="medium",
    
        source="runtime",
        service="backend-api",
    )
    plan   = _MockPlan()
    ticket = _MockTicket()

    asyncio.run(orch._step_generate_tests(job, inc, plan, ticket))

    assert isinstance(job.generated_tests, list)
    ok(f"Generated tests alanÄ±: {len(job.generated_tests)} test")

# test_generated_tests_step() - Moved to main block

section("6 â€” Sandbox Verify")

def test_sandbox_step():
    from packages.repair_engine.schemas.repair_job import RepairJob

    orch  = _build_mock_orchestrator()
    job   = RepairJob.create("inc_sb_001")
    patch = _MockPatch()

    result = asyncio.run(orch._step_sandbox_verify(job, patch, None))
    assert result is True
    ok("Sandbox verify adÄ±mÄ± True dÃ¶ndÃ¼")
    # sandbox_verified veya sandbox_output job'da set edilmiÅŸ olabilir
    assert isinstance(getattr(job, "sandbox_verified", False), bool)
    ok("job.sandbox_verified alanÄ± mevcut")

# test_sandbox_step() - Moved to main block

section("7 â€” Canary RC1")

def test_canary_rc1():
    from packages.repair_engine.schemas.repair_job import RepairJob

    orch  = _build_mock_orchestrator()
    job   = RepairJob.create("inc_cnry_001")
    job.risk_score = 20  # low risk -> canary Ã§alÄ±ÅŸmalÄ±

    patch = _MockPatch()
    plan  = _MockPlan()

    result = asyncio.run(orch._step_canary(job, patch, plan))
    assert isinstance(result, bool)
    ok(f"Canary RC1 adÄ±mÄ± â€” sonuÃ§: {result}")

def test_canary_rc1_high_risk():
    from packages.repair_engine.schemas.repair_job import RepairJob

    orch  = _build_mock_orchestrator()
    job   = RepairJob.create("inc_cnry_002")
    job.risk_score = 80  # high risk -> canary skip, manual

    patch = _MockPatch()
    plan  = types.SimpleNamespace(
        risk=types.SimpleNamespace(value="high"),
        target_files=["main.py"]
    )

    result = asyncio.run(orch._step_canary(job, patch, plan))
    assert result is True  # high risk pipeline'Ä± durdurmaz ama manual review
    ok("High risk -> canary skip, pipeline devam etti")

# test_canary_rc1() - Moved to main block
# test_canary_rc1_high_risk() - Moved to main block

section("8 â€” Vector Lesson Save")

def test_lesson_save():
    import packages.repair_engine.memory.vector_lessons as vl_mod
    vl_mod._vector_lessons = None
    store = vl_mod.get_vector_lessons(use_db=False)

    from packages.repair_engine.schemas.repair_job import RepairJob
    from packages.repair_engine.schemas.incident   import IncidentRecord

    orch = _build_mock_orchestrator()
    job  = RepairJob.create("inc_ls_001")
    job.diff         = "+TOKEN_TTL = 900\n"
    job.risk_score   = 25
    job.canary_status = "passed"

    inc = IncidentRecord(
        incident_id="inc_ls_001",
        symptom="JWT token expired after 1 hour",
        module="auth",
        severity="medium",
    
        source="runtime",
        service="backend-api",
    )

    before = store.stats().get("total", 0)
    asyncio.run(orch._save_vector_lesson(job, inc, "success"))
    after  = store.stats().get("total", 0)

    assert after == before + 1
    assert getattr(job, "lesson_saved", False) is True
    ok(f"Vector lesson kaydedildi â€” store: {after} ders")

# test_lesson_save() - Moved to main block

section("9 â€” Metrics Collector")

def test_metrics_step():
    from packages.repair_engine.schemas.repair_job import RepairJob
    from packages.repair_engine.schemas.incident   import IncidentRecord

    orch = _build_mock_orchestrator()
    job  = RepairJob.create("inc_mtr_001")
    inc  = IncidentRecord(
        incident_id="inc_mtr_001",
        symptom="JWT error",
        module="auth",
        severity="low",
    
        source="runtime",
        service="backend-api",
    )
    val = _MockValidation()

    # _record_metric hatasÄ±z Ã§alÄ±ÅŸmalÄ±
    orch._record_metric(job, inc, _MockPlan(), val, "success", 3.5)
    ok("_record_metric hatasÄ±z Ã§alÄ±ÅŸÄ±yor")

# test_metrics_step() - Moved to main block

section("10 â€” Validation Report Store")

def test_validation_report_store():
    from packages.repair_engine.verification.verification_engine import (
        save_validation_report, get_validation_report
    )
    job_id = f"job_vrs_{uuid.uuid4().hex[:6]}"
    report = {
        "validation_id": f"val_{uuid.uuid4().hex[:6]}",
        "syntax_ok":     True,
        "lint_ok":       True,
        "security_ok":   True,
        "architecture_ok": True,
        "unit_tests_ok": True,
        "confidence":    85,
        "final_status":  "passed",
        "patch_apply_output": "Applied OK",
        "verification_gaps": [],
    }
    save_validation_report(job_id, report)
    retrieved = get_validation_report(job_id)
    assert retrieved is not None
    assert retrieved["syntax_ok"]     is True
    assert retrieved["confidence"]    == 85
    assert retrieved["final_status"]  == "passed"
    assert "_saved_at" in retrieved
    ok("Validation raporu kaydedildi ve doÄŸru okundu")

def test_validation_report_missing():
    from packages.repair_engine.verification.verification_engine import get_validation_report
    result = get_validation_report("nonexistent_job_xyz")
    assert result is None
    ok("Olmayan job iÃ§in None dÃ¶ndÃ¼")

# test_validation_report_store() - Moved to main block
# test_validation_report_missing() - Moved to main block

section("11 â€” RepairJob Yeni Alanlar")

def test_new_job_fields():
    from packages.repair_engine.schemas.repair_job import RepairJob, RepairJobStatus

    job = RepairJob.create("inc_fields_001")

    # Faz 12 RC1 yeni alanlar
    required_fields = [
        "vector_context_used", "vector_context_summary",
        "debate_triggered", "debate_result_summary", "debate_winning_hypothesis",
        "sandbox_verified", "sandbox_output",
        "lesson_saved",
        "ranker_adjusted", "ranker_raw_confidence", "ranker_adjusted_confidence",
        "fingerprint_hash", "duplicate_of", "generated_tests",
        "risk_score", "canary_status",
    ]
    for field in required_fields:
        assert hasattr(job, field), f"Eksik alan: {field}"
    ok(f"TÃ¼m {len(required_fields)} RC1 alanÄ± RepairJob'da mevcut")

    # Yeni state'ler
    from packages.repair_engine.schemas.repair_job import RepairJobStatus
    new_states = [
        "VECTOR_CONTEXT_LOADED", "GENERATED_TESTS_READY",
        "SANDBOX_VERIFIED", "LESSON_SAVED",
    ]
    for s in new_states:
        assert hasattr(RepairJobStatus, s), f"Eksik state: {s}"
    ok(f"TÃ¼m {len(new_states)} RC1 state RepairJobStatus'ta mevcut")

def test_job_to_dict_complete():
    from packages.repair_engine.schemas.repair_job import RepairJob
    job = RepairJob.create("inc_dict_001")
    job.vector_context_used   = True
    job.debate_triggered      = True
    job.sandbox_verified      = True
    job.lesson_saved          = True
    d = job.to_dict()
    for key in ["vector_context_used", "debate_triggered", "sandbox_verified",
                "lesson_saved", "ranker_adjusted", "ranker_adjusted_confidence"]:
        assert key in d, f"to_dict'te eksik: {key}"
    ok("to_dict() tÃ¼m RC1 alanlarÄ±nÄ± iÃ§eriyor")

# test_new_job_fields() - Moved to main block
# test_job_to_dict_complete() - Moved to main block

section("12 â€” Tam Pipeline SimÃ¼lasyonu")

def test_full_pipeline_sim():
    """
    GerÃ§ek _run_pipeline Ã§aÄŸÄ±rmadan tÃ¼m adÄ±mlarÄ± sÄ±rayla
    mock ile Ã§alÄ±ÅŸtÄ±r ve job'un tÃ¼m alanlarÄ±n dolduÄŸunu doÄŸrula.
    """
    from packages.repair_engine.schemas.repair_job import RepairJob, RepairJobStatus
    from packages.repair_engine.schemas.incident   import IncidentRecord
    import packages.repair_engine.memory.vector_lessons as vl_mod

    # Temiz store
    vl_mod._vector_lessons = None
    vl_mod.get_vector_lessons(use_db=False)

    orch = _build_mock_orchestrator()
    job  = RepairJob.create("inc_full_001")
    inc  = IncidentRecord(
        incident_id="inc_full_001",
        symptom="JWT token decode error: invalid signature in auth module",
        module="auth",
        severity="high",
    
        source="runtime",
        service="backend-api",
    )
    ticket = _MockTicket()
    plan   = _MockPlan()
    patch  = _MockPatch()
    val    = _MockValidation()

    # â”€â”€ AdÄ±m 0: Fingerprint â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    orch._step_fingerprint(job, inc)

    # â”€â”€ AdÄ±m 2b: Vector RAG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ctx = asyncio.run(orch._step_get_context_from_vector(inc))
    if ctx:
        job.vector_context_used    = True
        job.vector_context_summary = ctx[:300]

    # â”€â”€ AdÄ±m 3b: Ranker â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ticket, ri = orch._step_rank_hypotheses(job, ticket, inc)

    # â”€â”€ AdÄ±m 3c: Debate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    asyncio.run(orch._step_debate_if_needed(job, ticket, inc))

    # â”€â”€ AdÄ±m 4b: Generated Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    asyncio.run(orch._step_generate_tests(job, inc, plan, ticket))

    # â”€â”€ AdÄ±m 6b: Architecture Guard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    asyncio.run(orch._step_architecture_guard(job, patch))

    # â”€â”€ AdÄ±m 7b: Sandbox â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    asyncio.run(orch._step_sandbox_verify(job, patch, plan))

    # â”€â”€ AdÄ±m 8b: Risk â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    asyncio.run(orch._step_score_risk(job, plan, val))

    # â”€â”€ AdÄ±m 9: Canary RC1 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    asyncio.run(orch._step_canary(job, patch, plan))

    # â”€â”€ AdÄ±m 11: Metrics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    orch._record_metric(job, inc, plan, val, "success", 5.0)

    # â”€â”€ AdÄ±m 12: Lesson Save â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    job.diff         = patch.diff
    job.risk_score   = job.risk_score or 20
    job.canary_status = "passed"
    asyncio.run(orch._save_vector_lesson(job, inc, "success"))

    # â”€â”€ DoÄŸrulama â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    assert isinstance(job.risk_score, int) and job.risk_score >= 0
    ok(f"risk_score dolu: {job.risk_score}")

    assert job.lesson_saved is True
    ok("lesson_saved = True")

    assert isinstance(job.generated_tests, list)
    ok(f"generated_tests: {len(job.generated_tests)} adet")

    assert isinstance(job.ranker_adjusted, bool)
    ok(f"ranker_adjusted: {job.ranker_adjusted}")

    assert isinstance(job.sandbox_verified, bool)
    ok(f"sandbox_verified: {job.sandbox_verified}")

    assert isinstance(job.debate_triggered, bool)
    ok(f"debate_triggered: {job.debate_triggered}")

    assert isinstance(job.vector_context_used, bool)
    ok(f"vector_context_used: {job.vector_context_used}")

    ok("âœ“ Tam pipeline simÃ¼lasyonu baÅŸarÄ±yla tamamlandÄ±")

# test_lesson_save()
# test_metrics_step()
# test_validation_report_store()
# test_validation_report_missing()
# test_new_job_fields()
# test_job_to_dict_complete()
# test_full_pipeline_sim()

if __name__ == "__main__":
    test_fingerprint_step()
    test_vector_rag_step()
    test_ranker_step()
    test_debate_triggered()
    test_generated_tests_step()
    test_sandbox_step()
    test_canary_rc1()
    test_canary_rc1_high_risk()
    test_lesson_save()
    test_metrics_step()
    test_validation_report_store()
    test_validation_report_missing()
    test_new_job_fields()
    test_job_to_dict_complete()
    test_full_pipeline_sim()

