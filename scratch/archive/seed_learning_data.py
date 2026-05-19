
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from libs.db.session import get_db_ctx, init_db
from libs.db.models.learning_models import ErrorFingerprint, LearningRecord, StrategyMemory
from libs.db.models.governance_models import PolicyProposal
from libs.db.models.lineage_models import DecisionLineage
from sqlalchemy import select

async def seed_learning():
    print("=== Seeding Learning Fabric & Governance Data (Lineage Update) ===")
    await init_db()
    
    async with get_db_ctx() as db:
        # 1. Seed Error Fingerprints
        fingerprint_id = uuid.uuid4()
        fingerprint = ErrorFingerprint(
            id=fingerprint_id,
            fingerprint_hash="ERR_API_TIMEOUT_504",
            error_family="API_TIMEOUT",
            service="workflow_api",
            component="GovernanceRouter",
            recurrence_count=12,
            first_seen_at=datetime.now(timezone.utc) - timedelta(days=2),
            last_seen_at=datetime.now(timezone.utc),
            meta_data={"stack_trace_snippet": "Timeout at reverse proxy", "impact": "High"}
        )
        db.add(fingerprint)
        
        # 2. Seed Strategy Memory
        strategy = StrategyMemory(
            id=uuid.uuid4(),
            component="GovernanceRouter",
            error_family="API_TIMEOUT",
            strategy_name="Adaptive_Backoff_Retry",
            success_count=45,
            failure_count=3,
            rollback_count=0,
            trust_score=0.92,
            state="trusted"
        )
        db.add(strategy)
        
        # 3. Seed Learning Records
        record = LearningRecord(
            id=uuid.uuid4(),
            fingerprint_id=fingerprint_id,
            strategy_used="Adaptive_Backoff_Retry",
            final_outcome="SUCCESS",
            created_at=datetime.now(timezone.utc) - timedelta(hours=5)
        )
        db.add(record)
        
        # 4. Seed Policy Proposals
        proposal = PolicyProposal(
            id=uuid.uuid4(),
            title="Auto-Scale API Latency Threshold",
            description="Recurring timeout detected in gateway. Proposal to increase wait from 5s to 8s for batch operations.",
            scope="AUTONOMOUS_LEARNING",
            status="pending",
            author_id="LearningEngine-V1",
            proposed_changes={
                "parameter": "gateway_timeout_s",
                "current_value": "5.0",
                "proposed_value": "8.0",
                "confidence": 0.88
            }
        )
        db.add(proposal)
        
        # 5. Seed Decision Lineage (to avoid 0 items in Audit page)
        lineage = DecisionLineage(
            id=uuid.uuid4(),
            decision_type="POLICY_CHANGE",
            component_name="LearningEngine",
            rationale="Detected recurring 504 errors in GovernanceRouter. Proposed timeout adjustment.",
            outcome="PROPOSED",
            confidence_score=0.95,
            trigger_event={"event_type": "ERROR_FINGERPRINT", "hash": "ERR_API_TIMEOUT_504"},
            created_at=datetime.now(timezone.utc) - timedelta(minutes=10)
        )
        db.add(lineage)
        
        await db.commit()
        print("Learning and Lineage data seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_learning())
