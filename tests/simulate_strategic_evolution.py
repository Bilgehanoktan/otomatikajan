
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from packages.persistence.session import session_scope
from packages.persistence.models import ImprovementOpportunity, CEOSuggestedTask, CEODecision
from core.ceo_engine import get_ceo_engine
from packages.packages.observability.logging import get_logger

logger = get_logger("verify_strategic")

async def simulate_architecture_gap():
    """
    Simulates a high-level architectural gap that requires a multi-step roadmap.
    """
    async with session_scope() as db:
        # 1. Create a mock opportunity
        # Pattern: 'governance_fragmentation'
        source_type = "arch_fragmentation"
        source_ref = "synaptic_cortex_isolation"
        phash = ImprovementOpportunity.generate_hash(source_type, source_ref)
        
        # Check if already exists to avoid duplicates
        existing_res = await packages.persistence.execute(select(ImprovementOpportunity).where(ImprovementOpportunity.pattern_hash == phash))
        existing_op = existing_res.scalars().first()
        if existing_op:
            logger.info(f"Simulation: Found existing opportunity {existing_op.id}. Cleaning up...")
            # Delete suggestions first due to FK
            from sqlalchemy import delete
            await packages.persistence.execute(delete(CEOSuggestedTask).where(CEOSuggestedTask.opportunity_id == existing_op.id))
            await packages.persistence.execute(delete(ImprovementOpportunity).where(ImprovementOpportunity.id == existing_op.id))
            await packages.persistence.commit()
            logger.info("Simulation: Cleanup complete.")
        
        op = ImprovementOpportunity(
            id=uuid.uuid4(),
            source_type=source_type,
            source_ref=source_ref,
            pattern_hash=phash,
            title="Bilisel Sinaps Paralanmas (Legacy Fragmentation)",
            description="SynapticCortex'in farkl modlleri arasnda verimsiz iletiim ve 'Reflective Brain' eksiklii tespit edildi.",
            severity="high",
            category="reliability",
            impact_score=85,
            urgency_score=70,
            confidence_score=0.9,
            priority_score=82,
            status="open"
        )
        packages.persistence.add(op)
        await packages.persistence.commit()
        logger.info(f"--- Simulation: Mock Opportunity Created: {op.id} ---")

        # 2. Trigger CEO Engine Scan
        ceo = get_ceo_engine()
        # We override the throttle for test
        ceo._throttle_auto_exec = False
        
        logger.info("--- CEO ENGINE SCAN BALATILIYOR... ---")
        scored_ops = await ceo.run_scan()
        
        # 3. Verify Results
        # Check suggestions
        res = await packages.persistence.execute(
            select(CEOSuggestedTask)
            .where(CEOSuggestedTask.opportunity_id == op.id)
            .order_by(CEOSuggestedTask.created_at.desc())
        )
        suggestions = res.scalars().all()
        
        if not suggestions:
            logger.error("!!! FAIL: No suggestions created by CEO Engine.")
            return

        roadmap_parent = next((s for s in suggestions if s.parent_id is None), None)
        if roadmap_parent:
            print(f"\n[SUCCESS] Roadmap Parent Found: {roadmap_parent.title}")
            print(f"Reasoning: {roadmap_parent.reasoning_summary}")
            print(f"Hierarchy: {roadmap_parent.plan_hierarchy}")
            
            # Check for steps
            steps = [s for s in suggestions if s.parent_id == roadmap_parent.id]
            print(f"Total Steps Found: {len(steps)}")
            
            for step in sorted(steps, key=lambda x: x.plan_hierarchy.get("step_index", 0)):
                status_icon = "✅" if step.status == "approved" else "⏳"
                print(f"  {status_icon} Step {step.plan_hierarchy.get('step_index')}: {step.title} ({step.status})")

            # Check for decisions
            dec_res = await packages.persistence.execute(select(CEODecision).where(CEODecision.opportunity_id == op.id))
            decisions = dec_res.scalars().all()
            for dec in decisions:
                print(f"Decision: {dec.decision_type} - {dec.decision_summary}")

        else:
            logger.warning("Simulation: No roadmap parent found, perhaps only a single task was created.")
            for s in suggestions:
                print(f"Single Task: {s.title} ({s.status})")

if __name__ == "__main__":
    asyncio.run(simulate_architecture_gap())
