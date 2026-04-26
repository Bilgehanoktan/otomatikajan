import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, ProjectStatus, LLMCostLog, OperationalIncident, SovereignEvidence, TaskPriority

async def inject_scenario_3():
    """
    Scenario 3: Economic Guardrails & Budget Circuit Breaker
    Simulates a project exceeding its budget and the AGI automatically halting it.
    """
    print("Initializing Scenario 3: Economic Guardrails (Budget Breaker)")
    
    async with AsyncSessionLocal() as session:
        # 1. Create a Project with a tight budget
        project_id = uuid.uuid4()
        project = Project(
            id=project_id,
            title="High-Scale Knowledge Retrieval",
            description="Deep crawl of archived neural networks",
            status=ProjectStatus.PAUSED, # Halted by budget
            budget_limit=1.50, # USD
            total_cost=1.52,
            priority=TaskPriority.HIGH,
            error_detail="ECON-LOCK: Budget threshold breached ($1.52 > $1.50). Scaling down resources."
        )
        session.add(project)
        
        # 2. Inject Cost Logs that exceed the budget
        print("   -> Injecting cost logs for project...")
        for i in range(5):
            cost_log = LLMCostLog(
                id=uuid.uuid4(),
                project_id=project_id,
                provider="openai",
                model="gpt-4o",
                agent_id="researcher-01",
                input_tokens=15000,
                output_tokens=5000,
                cost_usd=0.304, # Total 1.52
                latency_s=4.5,
                success=True,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=i*10)
            )
            session.add(cost_log)
        
        # 3. Create a Budget Breach Incident
        print("   -> Creating Budget Breach Incident...")
        incident = OperationalIncident(
            id=uuid.uuid4(),
            incident_type="budget_breach",
            severity="high",
            message="POL-LOCK: Economic circuit breaker triggered for Project 'High-Scale Knowledge Retrieval'.",
            status="investigating",
            project_id=project_id,
            payload={
                "current_total": 1.52,
                "limit": 1.50,
                "project_name": "High-Scale Knowledge Retrieval"
            }
        )
        session.add(incident)
        
        # 4. Seal Economic Evidence
        print("   -> Sealing Economic Evidence...")
        evidence = SovereignEvidence(
            id=uuid.uuid4(),
            evidence_type="economic_drift",
            severity="high",
            project_id=project_id,
            incident_id=incident.id,
            payload={
                "drift_ratio": 1.013,
                "mitigation_action": "Drain Resources / Pause Execution",
                "runway_impact": "-2.5h",
                "integrity_seal": "sha256:4d5e6f..."
            }
        )
        session.add(evidence)
        
        await session.commit()
        print("\nScenario 3 Injected Successfully!")
        print(f"   Project ID: {project_id}")
        print(f"   Incident ID: {incident.id}")

if __name__ == "__main__":
    asyncio.run(inject_scenario_3())
