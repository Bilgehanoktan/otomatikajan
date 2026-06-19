import uuid
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from services.governance.workflow_governor import WorkflowGovernor
from services.governance.incident_governor import IncidentGovernor
from services.governance.policy_governor import PolicyGovernor
from services.governance.repair_governor import RepairGovernor
from services.governance.approval_governor import ApprovalGovernor
from services.governance.governor_conflict_resolver import GovernorConflictResolver
from libs.db.repositories.meta_governor_repository import MetaGovernorRepo, GovernorConflictRepo
from services.governance.lineage_service import LineageService
from services.observability.logging import get_logger
from libs.db.session import get_db_ctx
from libs.db.models.core_models import FleetStatus, FleetCluster, AgentNode, AgentStatus
from sqlalchemy import select, func

logger = get_logger("governance.meta_governor")

class MetaGovernor:
    """
    Sovereign AGI Federated Governance Orchestrator.
    Tüm domain governor'ları koordine eder ve final meta-kararı verir.
    """

    def __init__(self):
        self.governors = {
            "WORKFLOW": WorkflowGovernor(),
            "INCIDENT": IncidentGovernor(),
            "POLICY": PolicyGovernor(),
            "REPAIR": RepairGovernor(),
            "APPROVAL": ApprovalGovernor()
        }
        self.resolver = GovernorConflictResolver()

    async def scan_project(self, project_id: UUID) -> Dict[str, Any]:
        """
        Bir projeyi tüm domain governor'lar üzerinden tarar ve meta karar verir.
        """
        logger.info(f"[MetaGovernor] Scanning project {project_id}")
        
        # Faz 9: Güncel politikaları yükle
        from services.governance.governor_policy_config import GovernorPolicyConfig
        
        # 1. Tüm governor'lardan karar topla
        domain_decisions = {}
        async with get_db_ctx() as session:
            await GovernorPolicyConfig.refresh_overrides(session)
            
            # Faz 12: Fleet Level Guard
            # Eğer proje bir cluster'a atanmışsa ve o cluster FROZEN ise işlemi kısıtla
            from libs.db.models.core_models import Project
            project_db = await session.get(Project, project_id)
            if project_db:
                # Get cluster status via assignments
                from libs.db.models.core_models import FleetAssignment
                cluster_status_query = select(FleetCluster.status).join(AgentNode).join(FleetAssignment).where(FleetAssignment.project_id == project_id)
                cluster_status = (await session.execute(cluster_status_query)).scalar()
                
                if cluster_status == FleetStatus.FROZEN:
                    logger.warning(f"[MetaGovernor] Cluster is FROZEN for project {project_id}. Blocking execution.")
                    return {
                        "project_id": str(project_id),
                        "final_decision": {"recommended_decision": "BLOCK", "reason": "Fleet Cluster Frozen"},
                        "conflicts": [],
                        "constraints": ["FLEET_LOCK"]
                    }
            
            for name, gov in self.governors.items():
                try:
                    # Faz 8: Resilience wrapper ile çalıştır
                    decision = await gov.run_with_resilience(session, project_id)
                    domain_decisions[name] = decision
                except Exception as e:
                    logger.error(f"[MetaGovernor] Governor {name} failed for {project_id}: {e}")

        # 2. Çakışmaları tespit et
        start_resolve = datetime.now(timezone.utc)
        conflicts = self.resolver.detect_conflicts(domain_decisions)
        
        # 3. Çözüm üret
        final_decision, constraints = self.resolver.resolve(domain_decisions, conflicts)
        
        # Faz 8: Meta SLO ölçümü
        resolve_latency = int((datetime.now(timezone.utc) - start_resolve).total_seconds() * 1000)
        async with get_db_ctx() as session:
            from services.governance.governor_slo_monitor import GovernorSloMonitor
            from libs.db.models.governance_models import GovernorDomain
            await GovernorSloMonitor.record_latency(session, GovernorDomain.META, "meta_resolve", resolve_latency)
            await session.commit()
        
        # 4. Kaydet ve Lineage yaz
        async with get_db_ctx() as session:
            # Çakışmaları kaydet
            for conflict in conflicts:
                await GovernorConflictRepo.save_conflict(session, project_id, conflict)
            
            # Meta kararı kaydet
            meta_record = await MetaGovernorRepo.save_meta_decision(
                session, 
                project_id, 
                final_decision, 
                constraints
            )
            
            # Lineage
            await LineageService.log_meta_governor_decision(
                project_id=project_id,
                domain_decisions=domain_decisions,
                final_decision=final_decision,
                conflicts=conflicts,
                constraints=constraints,
                db=session
            )
            
            await session.commit()

        logger.info(f"[MetaGovernor] Final decision for {project_id}: {final_decision['recommended_decision']}")
        return {
            "project_id": str(project_id),
            "final_decision": final_decision,
            "conflicts": conflicts,
            "constraints": constraints
        }
