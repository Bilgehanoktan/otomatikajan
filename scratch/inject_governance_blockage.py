import asyncio
import uuid
from datetime import datetime, timezone
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import WorkflowEvent, OperationalIncident, SovereignEvidence, Project, ProjectStatus
from services.governance.policy.policy_engine import PolicyEngine, AutomationLevel
from services.repair.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
from services.repair.schemas.patch_plan import PatchPlan, RiskLevel
from services.repair.schemas.validation import ValidationReport

async def inject_scenario_2():
    """
    Scenario 2: Constitutional Governance Blockage
    Simulates an attempt to modify a protected 'auth' module and shows how the system blocks it.
    """
    print("Initializing Scenario 2: Constitutional Governance Blockage (Safety Lock)")
    
    # 1. Setup the Policy Engine
    engine = PolicyEngine()
    
    # 2. Create a "Forbidden" Ticket and Plan
    ticket = DiagnosisTicket(
        ticket_id=str(uuid.uuid4()),
        incident_id="AUTH_LEAK_01",
        rationale="Potential leak in session handling",
        classification=ProblemClass.AUTH_FAILURE,
        severity="critical",
        recommended_mode=RepairMode.AUTO_PATCH_PR
    )
    
    plan = PatchPlan(
        plan_id=str(uuid.uuid4()),
        ticket_id=ticket.ticket_id,
        target_files=["auth/session_manager.py"], # This is in BLOCKED_MODULES
        risk=RiskLevel.MEDIUM,
        rationale="Update session hash logic"
    )
    
    validation = ValidationReport(
        validation_id=str(uuid.uuid4()),
        patch_plan_id=plan.plan_id,
        syntax_ok=True,
        security_ok=True,
        architecture_ok=True,
        confidence=85
    )
    
    # 3. Evaluate via Policy Engine
    print("   -> Evaluating policy for auth module modification...")
    decision = engine.evaluate_patch(ticket, plan, validation, job_id="gov_block_test")
    
    print(f"   -> Decision: Allowed={decision.allowed}, Action={decision.recommended_action}")
    print(f"   -> Reasons: {decision.blocking_reasons}")
    
    # 4. Record the blockage in the database
    async with AsyncSessionLocal() as session:
        # Create a project representing this attempt
        project = Project(
            id=uuid.uuid4(),
            title="Security Patch: Session Logic",
            status=ProjectStatus.FAILED,
            description="Autonomous attempt to patch auth/session_manager.py",
            error_detail="POL-LOCK: Access to protected module 'auth' is forbidden by constitution."
        )
        session.add(project)
        
        # Log the Policy Rejection Event
        event = WorkflowEvent(
            id=uuid.uuid4(),
            project_id=project.id,
            event_type="policy_violation",
            operator_id="governance_engine",
            payload=decision.to_dict(),
            created_at=datetime.now(timezone.utc)
        )
        session.add(event)
        
        # Create a Governance Incident
        incident = OperationalIncident(
            id=uuid.uuid4(),
            incident_type="safety_violation",
            severity="critical",
            message="POL-LOCK: Autonomous agent attempted to modify protected identity module.",
            status="resolved", # Automatically resolved by blocking it
            project_id=project.id,
            payload={
                "target_module": "auth",
                "policy_id": "STRICT_IDENTITY_PROTECTION",
                "action_taken": "Hard Block"
            }
        )
        session.add(incident)
        
        # Seal Evidence
        evidence = SovereignEvidence(
            id=uuid.uuid4(),
            evidence_type="governance_lock",
            severity="critical",
            project_id=project.id,
            incident_id=incident.id,
            payload={
                "decision": "DENIED",
                "lock_reason": decision.blocking_reasons[0],
                "integrity_seal": "sha256:8b2a3c..."
            }
        )
        session.add(evidence)
        
        await session.commit()
        print("\nScenario 2 Injected Successfully!")
        print(f"   Project ID: {project.id}")
        print(f"   Incident ID: {incident.id}")

if __name__ == "__main__":
    asyncio.run(inject_scenario_2())
