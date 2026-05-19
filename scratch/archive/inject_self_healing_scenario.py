import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import WorkflowEvent, OperationalIncident, ImprovementOpportunity, SystemImprovement, SovereignEvidence

async def inject_scenario_1():
    """
    Scenario 1: Performance Drift in Orchestrator
    Simulates a recurring latency issue and triggers the Self-Healing loop.
    """
    print("Initializing Scenario 1: Self-Healing Infrastructure (Latency Drift)")
    
    async with AsyncSessionLocal() as session:
        # 1. Create a dummy Project for this scenario
        project_id = uuid.uuid4()
        
        # 2. Inject recurring latency events
        print("   -> Injecting latency events into workflow_events...")
        for i in range(12):
            event = WorkflowEvent(
                id=uuid.uuid4(),
                project_id=None, # System-wide event
                event_type="step_failed",
                step_id="orchestrator.dispatch_task",
                operator_id="system",
                payload={
                    "error": "Latency threshold exceeded (1500ms > 500ms)",
                    "latency_ms": 1500 + random.randint(0, 500),
                    "region": "us-east-1"
                },
                created_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 60))
            )
            session.add(event)
        
        # 3. Create an Operational Incident
        print("   -> Creating Operational Incident...")
        incident = OperationalIncident(
            id=uuid.uuid4(),
            incident_type="performance_drift",
            severity="high",
            message="Recurring latency drift detected in orchestrator.dispatch_task (us-east-1)",
            status="open",
            payload={
                "affected_node": "dispatch-01",
                "drift_magnitude": "300%",
                "anomaly_score": 0.89
            }
        )
        session.add(incident)
        
        # 4. Create an Improvement Opportunity
        print("   -> Creating Improvement Opportunity...")
        pattern_hash = ImprovementOpportunity.generate_hash("agent_failure", "orchestrator.dispatch_task:Latency threshold exceeded")
        opp = ImprovementOpportunity(
            id=uuid.uuid4(),
            source_type="agent_failure",
            source_ref="orchestrator.dispatch_task",
            title="Optimize Dispatcher Latency",
            description="Recurring latency drift in us-east-1 detected. Analysis suggests a bottleneck in task dispatching logic.",
            severity="high",
            category="performance",
            evidence_detail="12 occurrences in the last 60 minutes. Mean latency: 1750ms.",
            pattern_hash=pattern_hash,
            status="open"
        )
        session.add(opp)
        
        # 5. Propose a Patch (SystemImprovement)
        print("   -> Proposing Elite Patch (SystemImprovement)...")
        patch = SystemImprovement(
            id=uuid.uuid4(),
            opportunity_id=opp.id,
            target_file="services/orchestration/application/dispatcher.py",
            instruction="Implement predictive caching for task dispatching to reduce redundant DB lookups.",
            proposed_patch="""--- dispatcher.py
+++ dispatcher.py
@@ -12,4 +12,12 @@
-    def dispatch(self, task):
-        data = db.fetch(task.id)
-        return self.send(data)
+    def dispatch(self, task):
+        # ELITE CACHE IMPLEMENTATION (Self-Healed)
+        if cache.has(task.id):
+            return self.send(cache.get(task.id))
+        
+        data = db.fetch(task.id)
+        cache.set(task.id, data, ttl=300)
+        return self.send(data)""",
            status="pending",
            risk_score=0.12,
            test_results={
                "valid": True,
                "shadow_score": 0.98,
                "latency_reduction": "45%"
            }
        )
        session.add(patch)
        
        # 6. Add Sovereign Evidence (Lineage)
        print("   -> Sealing Evidence Chain...")
        evidence = SovereignEvidence(
            id=uuid.uuid4(),
            evidence_type="self_healing",
            severity="high",
            incident_id=incident.id,
            improvement_id=patch.id,
            payload={
                "logic": "Predictive Latency Mitigation",
                "causality": "Drift detected -> Opportunity mapped -> Shadow verified",
                "integrity_hash": "sha256:7f3aa9..."
            }
        )
        session.add(evidence)
        
        await session.commit()
        print("\nScenario 1 Injected Successfully!")
        print(f"   Incident ID: {incident.id}")
        print(f"   Opportunity ID: {opp.id}")
        print(f"   Patch ID: {patch.id}")
        print("\nRefresh the Cockpit to see the autonomous response in action.")

if __name__ == "__main__":
    asyncio.run(inject_scenario_1())
