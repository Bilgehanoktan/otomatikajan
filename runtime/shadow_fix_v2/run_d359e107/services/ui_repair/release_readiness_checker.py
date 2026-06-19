import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import (
    UIReleaseReadinessCheck, ReleaseStatus, UISmokeRun,
    UIRepairCase, UIProviderHealth, UIThirdPartyRiskAssessment, UIAutoPatchExecution,
    UIKnowledgeNode, UIKnowledgeEdge, UIRecoveryProofPack, UIClusterProfile,
    UIFinalIntegrationAudit
)
from services.ui_repair.service import UIRepairService

logger = logging.getLogger(__name__)

class ReleaseReadinessChecker:
    """Phase 30: Evaluates the system against production readiness standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_readiness(self) -> List[UIReleaseReadinessCheck]:
        """Runs a comprehensive readiness check across multiple categories."""
        status_value = lambda value: getattr(value, "value", value)
        summary = await UIRepairService(self.db).get_dashboard_summary()
        total_routes = int(summary["total_routes"])
        failing_routes = int(summary["failing_routes"])
        last_smoke = (
            await self.db.execute(select(UISmokeRun).order_by(UISmokeRun.started_at.desc()).limit(1))
        ).scalar_one_or_none()
        open_cases = int(summary["open_cases"])
        governance_waiting = (
            await self.db.execute(
                select(func.count(UIRepairCase.id)).where(UIRepairCase.status == "WAITING_GOVERNANCE")
            )
        ).scalar() or 0
        degraded_providers = (
            await self.db.execute(
                select(func.count(UIProviderHealth.id)).where(UIProviderHealth.status.in_(["DEGRADED", "UNAVAILABLE"]))
            )
        ).scalar() or 0
        high_tool_risks = (
            await self.db.execute(
                select(func.count(UIThirdPartyRiskAssessment.id)).where(UIThirdPartyRiskAssessment.risk_level.in_(["HIGH", "CRITICAL"]))
            )
        ).scalar() or 0
        blocked_autopatch = (
            await self.db.execute(
                select(func.count(UIAutoPatchExecution.id)).where(UIAutoPatchExecution.status.in_(["FAILED", "PREFLIGHT_BLOCKED", "ROLLBACK_REQUIRED"]))
            )
        ).scalar() or 0
        pending_autopatch = (
            await self.db.execute(
                select(func.count(UIAutoPatchExecution.id)).where(UIAutoPatchExecution.status.in_(["GOVERNANCE_REQUESTED", "VERIFICATION_RUNNING", "APPLYING"]))
            )
        ).scalar() or 0
        knowledge_nodes = (await self.db.execute(select(func.count(UIKnowledgeNode.id)))).scalar() or 0
        knowledge_edges = (await self.db.execute(select(func.count(UIKnowledgeEdge.id)))).scalar() or 0
        proof_packs = (await self.db.execute(select(func.count(UIRecoveryProofPack.id)))).scalar() or 0
        clusters = (await self.db.execute(select(func.count(UIClusterProfile.id)))).scalar() or 0
        latest_audit = (
            await self.db.execute(select(UIFinalIntegrationAudit).order_by(UIFinalIntegrationAudit.created_at.desc()).limit(1))
        ).scalar_one_or_none()

        categories: List[Dict[str, Any]] = []

        backend_blockers: List[str] = []
        backend_warnings: List[str] = []
        if not last_smoke:
            backend_warnings.append("No smoke run has been recorded yet.")
        elif status_value(last_smoke.status) != "COMPLETED":
            backend_blockers.append(f"Latest smoke run status is {status_value(last_smoke.status)}.")
        backend_score = 100.0 if not backend_blockers else 60.0
        categories.append({
            "category": "Backend API",
            "score": backend_score,
            "blockers": backend_blockers,
            "warnings": backend_warnings,
            "recommendation": "Keep backend health and smoke run green before release lock.",
        })

        ui_blockers: List[str] = []
        ui_warnings: List[str] = []
        if failing_routes > 0:
            ui_blockers.append(f"{failing_routes} failing routes remain in the active surface.")
        if open_cases > 0:
            ui_warnings.append(f"{open_cases} unresolved UI repair cases remain open.")
        ui_score = max(0.0, 100.0 - (failing_routes * 20.0) - (open_cases * 5.0))
        categories.append({
            "category": "UI Dashboard",
            "score": ui_score if total_routes > 0 else 70.0,
            "blockers": ui_blockers,
            "warnings": ui_warnings,
            "recommendation": "Resolve active route failures and clear open UI cases.",
        })

        governance_blockers: List[str] = []
        governance_warnings: List[str] = []
        if governance_waiting > 0:
            governance_blockers.append(f"{governance_waiting} cases are still waiting for governance.")
        if pending_autopatch > 0:
            governance_warnings.append(f"{pending_autopatch} autopatch executions are still pending approval or verification.")
        governance_score = max(0.0, 100.0 - (governance_waiting * 15.0) - (pending_autopatch * 5.0))
        categories.append({
            "category": "Governance",
            "score": governance_score,
            "blockers": governance_blockers,
            "warnings": governance_warnings,
            "recommendation": "Close governance queues before sealing the release candidate.",
        })

        tool_blockers: List[str] = []
        tool_warnings: List[str] = []
        if degraded_providers > 0:
            tool_warnings.append(f"{degraded_providers} providers are degraded or unavailable.")
        if high_tool_risks > 0:
            tool_warnings.append(f"{high_tool_risks} external tool assessments are HIGH or CRITICAL risk.")
        tool_score = max(0.0, 100.0 - (degraded_providers * 15.0) - (high_tool_risks * 8.0))
        categories.append({
            "category": "Tool Governance",
            "score": tool_score,
            "blockers": tool_blockers,
            "warnings": tool_warnings,
            "recommendation": "Stabilize providers or force approval-only mode for risky tool paths.",
        })

        autopatch_blockers: List[str] = []
        autopatch_warnings: List[str] = []
        if blocked_autopatch > 0:
            autopatch_blockers.append(f"{blocked_autopatch} autopatch executions are blocked or failed.")
        if pending_autopatch > 0:
            autopatch_warnings.append(f"{pending_autopatch} autopatch executions are still in flight.")
        autopatch_score = max(0.0, 100.0 - (blocked_autopatch * 20.0) - (pending_autopatch * 5.0))
        categories.append({
            "category": "Autonomous Patching",
            "score": autopatch_score,
            "blockers": autopatch_blockers,
            "warnings": autopatch_warnings,
            "recommendation": "Only verified and governance-cleared autopatch executions should reach apply.",
        })

        knowledge_blockers: List[str] = []
        knowledge_warnings: List[str] = []
        if knowledge_nodes == 0 or knowledge_edges == 0:
            knowledge_warnings.append("Knowledge graph has insufficient nodes or edges for confident recall.")
        knowledge_score = 100.0 if knowledge_nodes > 0 and knowledge_edges > 0 else 70.0
        categories.append({
            "category": "Knowledge Graph",
            "score": knowledge_score,
            "blockers": knowledge_blockers,
            "warnings": knowledge_warnings,
            "recommendation": "Populate knowledge graph evidence before relying on similarity and causal recall.",
        })

        resilience_blockers: List[str] = []
        resilience_warnings: List[str] = []
        if proof_packs == 0:
            resilience_warnings.append("No recovery proof pack has been generated.")
        if clusters == 0:
            resilience_warnings.append("Federation clusters are not registered yet.")
        resilience_score = 100.0 - (15.0 if proof_packs == 0 else 0.0) - (10.0 if clusters == 0 else 0.0)
        categories.append({
            "category": "Operational Resilience",
            "score": max(0.0, resilience_score),
            "blockers": resilience_blockers,
            "warnings": resilience_warnings,
            "recommendation": "Generate resilience evidence and validate failover before release lock.",
        })

        audit_blockers: List[str] = []
        audit_warnings: List[str] = []
        if latest_audit and status_value(latest_audit.status) == "FAILED":
            audit_blockers.extend(latest_audit.failed_modules_json or [])
        if latest_audit and latest_audit.warnings_json:
            audit_warnings.extend(latest_audit.warnings_json)
        if not latest_audit:
            audit_warnings.append("No final integration audit has been recorded yet.")
        audit_score = 100.0 if latest_audit and status_value(latest_audit.status) == "PASSED" else 75.0 if latest_audit else 65.0
        categories.append({
            "category": "Integration Audit",
            "score": audit_score,
            "blockers": audit_blockers,
            "warnings": audit_warnings,
            "recommendation": "Run and pass final integration audit before creating release lock.",
        })

        results = []
        for entry in categories:
            blockers = entry["blockers"]
            warnings = entry["warnings"]
            status = ReleaseStatus.PASSED
            if blockers:
                status = ReleaseStatus.BLOCKED
            elif warnings or entry["score"] < 90:
                status = ReleaseStatus.WARNING

            check = UIReleaseReadinessCheck(
                check_key=f"READINESS-{entry['category'].upper().replace(' ', '-')}-{uuid.uuid4().hex[:4].upper()}",
                category=entry["category"],
                status=status,
                score=entry["score"],
                blockers_json=blockers,
                warnings_json=warnings,
                recommendation=entry["recommendation"],
            )
            self.db.add(check)
            results.append(check)

        await self.db.commit()
        return results

    async def get_overall_readiness_score(self) -> float:
        """Calculates the aggregate readiness score."""
        stmt = select(UIReleaseReadinessCheck).order_by(UIReleaseReadinessCheck.created_at.desc()).limit(10)
        result = await self.db.execute(stmt)
        checks = result.scalars().all()
        
        if not checks:
            return 0.0
        
        total_score = sum(c.score for c in checks)
        return total_score / len(checks)

    async def get_readiness_summary(self) -> Dict[str, Any]:
        """Provides a summary of readiness across all categories."""
        stmt = select(UIReleaseReadinessCheck).order_by(UIReleaseReadinessCheck.created_at.desc()).limit(10)
        result = await self.db.execute(stmt)
        checks = result.scalars().all()
        
        blockers = []
        warnings = []
        for c in checks:
            blockers.extend(c.blockers_json)
            warnings.extend(c.warnings_json)
            
        score = sum(c.score for c in checks) / len(checks) if checks else 0.0
        
        status = ReleaseStatus.RELEASE_CANDIDATE
        if score < 90:
            status = ReleaseStatus.WARNING
        if blockers:
            status = ReleaseStatus.BLOCKED

        return {
            "score": score,
            "status": status,
            "blockers": blockers,
            "warnings": warnings,
            "check_count": len(checks)
        }
