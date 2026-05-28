import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, '.')

from libs.db.session import AsyncSessionLocal
from libs.db.models.repair_models import (
    RepairBenchmarkRun,
    RepairTournament,
    RepairCandidate,
    VerifierResult,
    SelfTuningSuggestion,
    RepairMemory
)
from libs.db.models.lineage_models import DecisionLineage

async def seed_repair_mesh():
    print("Seeding premium Repair Lab & Verifier Mesh data...")
    async with AsyncSessionLocal() as db:
        # Clear existing data to prevent integrity errors
        from sqlalchemy import delete, text
        
        # Disable foreign keys temporarily for clean delete/reseed
        dialect_name = db.bind.dialect.name
        if dialect_name == "sqlite":
            await db.execute(text("PRAGMA foreign_keys = OFF;"))
        elif dialect_name == "postgresql":
            await db.execute(text("SET session_replication_role = 'replica';"))
            
        await db.execute(delete(VerifierResult))
        await db.execute(delete(RepairCandidate))
        await db.execute(delete(RepairTournament))
        await db.execute(delete(RepairBenchmarkRun))
        await db.execute(delete(SelfTuningSuggestion))
        await db.execute(delete(RepairMemory))
        await db.execute(delete(DecisionLineage))
        
        now = datetime.now(timezone.utc)
        
        # 1. Benchmark Runs
        run1_id = "run_" + uuid.uuid4().hex[:12]
        run2_id = "run_" + uuid.uuid4().hex[:12]
        
        r1 = RepairBenchmarkRun(
            id=uuid.uuid4(),
            run_id=run1_id,
            project_id="sovereign-core",
            cluster_id="local-lab",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1, minutes=45),
            total_cases=12,
            success_rate=0.833,
            avg_score=0.915,
            total_validation_cost=2.45,
            total_validation_time=900.0,
            status="completed"
        )
        
        r2 = RepairBenchmarkRun(
            id=uuid.uuid4(),
            run_id=run2_id,
            project_id="workflows-api",
            cluster_id="local-lab",
            start_time=now - timedelta(minutes=15),
            total_cases=5,
            success_rate=0.0,
            avg_score=0.0,
            total_validation_cost=0.50,
            total_validation_time=120.0,
            status="running"
        )
        db.add_all([r1, r2])
        await db.flush()
        
        # 2. Tournaments
        tour1_id = "tour_" + uuid.uuid4().hex[:12]
        tour2_id = "tour_" + uuid.uuid4().hex[:12]
        
        t1 = RepairTournament(
            id=uuid.uuid4(),
            tournament_id=tour1_id,
            run_id=run1_id,
            incident_id="incident_auth_fail_091",
            project_id="sovereign-core",
            cluster_id="local-lab",
            winner_candidate_id="cand_conservative_01",
            winner_score=0.985,
            total_candidates=3,
            created_at=now - timedelta(hours=1, minutes=50)
        )
        
        t2 = RepairTournament(
            id=uuid.uuid4(),
            tournament_id=tour2_id,
            run_id=run1_id,
            incident_id="incident_jwt_expiry_042",
            project_id="sovereign-core",
            cluster_id="local-lab",
            winner_candidate_id="cand_radical_02",
            winner_score=0.960,
            total_candidates=2,
            created_at=now - timedelta(hours=1, minutes=20)
        )
        db.add_all([t1, t2])
        await db.flush()
        
        # 3. Candidates & Verifier Results
        # For Tournament 1 (Winner is cand_c1)
        cand_c1_id = "cand_conservative_01"
        cand_c2_id = "cand_radical_01"
        
        c1 = RepairCandidate(
            id=uuid.uuid4(),
            candidate_id=cand_c1_id,
            tournament_id=tour1_id,
            strategy="conservative",
            candidate_type="code",
            patch_diff="--- services/auth/jwt_auth.py\n+++ services/auth/jwt_auth.py\n- ACCESS_MINUTES = 1440\n+ ACCESS_MINUTES = 60",
            patch_signature="jwt_auth:conservative",
            risk_score=0.1,
            final_score=0.985,
            canary_outcome="success",
            total_validation_cost=0.45,
            total_validation_time=120.0,
            status="winner"
        )
        
        c2 = RepairCandidate(
            id=uuid.uuid4(),
            candidate_id=cand_c2_id,
            tournament_id=tour1_id,
            strategy="radical",
            candidate_type="code",
            patch_diff="--- services/auth/jwt_auth.py\n+++ services/auth/jwt_auth.py\n- ACCESS_MINUTES = 1440\n+ ACCESS_MINUTES = 15\n+ def force_logout_all(): pass",
            patch_signature="jwt_auth:radical",
            risk_score=0.6,
            final_score=0.740,
            canary_outcome="rollback",
            rollback_reason="Forced logout caused API connection disruption during user sessions.",
            total_validation_cost=0.85,
            total_validation_time=250.0,
            status="rejected"
        )
        db.add_all([c1, c2])
        await db.flush()
        
        # Verifier Results for Candidate 1
        verifiers = [
            ("Linter & Code Quality", 1.0, True, {"build": "successful", "warnings": 0, "lint": "clean"}),
            ("Pytest Framework", 0.98, True, {"tests_total": 49, "tests_passed": 48, "coverage": "87.5%"}),
            ("Playwright E2E UI Suite", 1.0, True, {"scenarios": 12, "passed": 12, "flaky": 0}),
            ("Security Vulnerability Scan", 0.95, True, {"secrets_found": 0, "ssrf_guard": "active"}),
            ("Axiology & Policy Auditor", 1.0, True, {"alignment": "perfect", "rules_checked": 8})
        ]
        
        for name, score, passed, details in verifiers:
            vr = VerifierResult(
                id=uuid.uuid4(),
                result_id="vr_" + uuid.uuid4().hex[:12],
                candidate_id=cand_c1_id,
                verifier_name=name,
                score=score,
                passed=passed,
                details=details,
                timestamp=now - timedelta(hours=1, minutes=48)
            )
            db.add(vr)
            
        # Verifier Results for Candidate 2 (Failing E2E UI Suite and radical strategy has some security warning)
        verifiers_c2 = [
            ("Linter & Code Quality", 0.90, True, {"build": "successful", "warnings": 4}),
            ("Pytest Framework", 0.95, True, {"tests_total": 49, "tests_passed": 46}),
            ("Playwright E2E UI Suite", 0.40, False, {"scenarios": 12, "passed": 5, "failures": ["Login page timed out"]}),
            ("Security Vulnerability Scan", 0.70, True, {"owasp_alerts": 1, "warning": "Unused import of force_logout"}),
            ("Axiology & Policy Auditor", 0.80, True, {"alignment": "high"})
        ]
        
        for name, score, passed, details in verifiers_c2:
            vr = VerifierResult(
                id=uuid.uuid4(),
                result_id="vr_" + uuid.uuid4().hex[:12],
                candidate_id=cand_c2_id,
                verifier_name=name,
                score=score,
                passed=passed,
                details=details,
                timestamp=now - timedelta(hours=1, minutes=40)
            )
            db.add(vr)
            
        # 4. Self Tuning Suggestions
        s1 = SelfTuningSuggestion(
            id=uuid.uuid4(),
            suggestion_id="sug_" + uuid.uuid4().hex[:12],
            parameter_name="AUTO_REPAIR_RISK_THRESHOLD",
            current_value=0.35,
            proposed_value=0.50,
            reason="Canary metrics show 99.2% accuracy. Elevating threshold enables autonomous fixes on moderately complex UI issues without blocking operator queue.",
            expected_impact="Reduces operator approval bottleneck by 35% on low-risk styled UI patches.",
            status="pending",
            created_at=now - timedelta(hours=3)
        )
        
        s2 = SelfTuningSuggestion(
            id=uuid.uuid4(),
            suggestion_id="sug_" + uuid.uuid4().hex[:12],
            parameter_name="VERIFIER_MAX_LATENCY_LIMIT",
            current_value=3.0,
            proposed_value=2.0,
            reason="Aggregated matrix results show average validation completes under 1.5 seconds. Tightening the latency limit optimizes overall rebalance times.",
            expected_impact="Saves average of 1.2s per test run during active local watch iteration loops.",
            status="applied",
            created_at=now - timedelta(days=2)
        )
        db.add_all([s1, s2])
        
        # 5. Repair Memories
        m1 = RepairMemory(
            id=uuid.uuid4(),
            memory_id="mem_" + uuid.uuid4().hex[:12],
            incident_id="incident_auth_fail_091",
            project_id="sovereign-core",
            cluster_id="local-lab",
            patch_signature="jwt_auth:conservative",
            subsystem="authentication",
            outcome="success",
            score=0.985,
            recorded_at=now - timedelta(hours=1, minutes=45)
        )
        
        m2 = RepairMemory(
            id=uuid.uuid4(),
            memory_id="mem_" + uuid.uuid4().hex[:12],
            incident_id="incident_jwt_expiry_042",
            project_id="sovereign-core",
            cluster_id="local-lab",
            patch_signature="jwt_auth:radical",
            subsystem="security",
            outcome="failure",
            failure_reason="Playwright E2E UI Suite detected session termination crash.",
            verifier_rejections=["Playwright E2E UI Suite"],
            score=0.740,
            recorded_at=now - timedelta(hours=1, minutes=15)
        )
        db.add_all([m1, m2])
        
        # 6. Decision Lineage
        dl = DecisionLineage(
            id=uuid.uuid4(),
            decision_type="SYSTEM_EVOLUTION",
            component_name="repair_lab",
            trigger_event={"reason": "Benchmark run completed successfully"},
            rationale="Auto-calibrated verifier weights after successful run conservative repair of token expiration validation.",
            outcome="PROMOTED",
            confidence_score=0.94,
            created_at=now - timedelta(hours=1),
            integrity_hash="repair-mesh-lineage-01"
        )
        db.add(dl)
        
        # Disable replication role back to origin for postgres
        if dialect_name == "postgresql":
            await db.execute(text("SET session_replication_role = 'origin';"))
            
        await db.commit()
        print("Premium Repair Lab and Verifier Mesh data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_repair_mesh())
