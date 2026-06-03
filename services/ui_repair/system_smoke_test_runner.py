import logging
from time import perf_counter
from typing import List
from datetime import datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIBudgetPolicy,
    UIClusterProfile,
    UICostEvent,
    UIKnowledgeEdge,
    UIKnowledgeNode,
    UIPolicyRule,
    UIRecoveryProofPack,
    UISecurityPostureFinding,
    UISovereignIdentity,
)
from services.ui_repair.schemas import UISmokeTestResultSchema
from services.ui_repair.service import UIRepairService

logger = logging.getLogger(__name__)

class SystemSmokeTestRunner:
    """Phase 30: Executes core system smoke tests for final verification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _build_result(self, module_name: str, probe) -> UISmokeTestResultSchema:
        started = perf_counter()
        try:
            error_message = await probe()
            status = "PASSED" if error_message is None else "FAILED"
            return UISmokeTestResultSchema(
                module_name=module_name,
                status=status,
                latency_ms=max(1, int((perf_counter() - started) * 1000)),
                error_message=error_message,
                last_run_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.exception("System smoke probe failed for %s", module_name)
            await self.db.rollback()
            return UISmokeTestResultSchema(
                module_name=module_name,
                status="FAILED",
                latency_ms=max(1, int((perf_counter() - started) * 1000)),
                error_message=str(exc),
                last_run_at=datetime.now(timezone.utc),
            )

    async def run_smoke_tests(self) -> List[UISmokeTestResultSchema]:
        """Runs data-driven health checks across critical modules."""
        logger.info("Running system smoke tests...")

        async def probe_health_endpoint() -> str | None:
            await self.db.execute(text("SELECT 1"))
            return None

        async def probe_ui_repair() -> str | None:
            summary = await UIRepairService(self.db).get_dashboard_summary()
            if summary["total_routes"] == 0:
                return "No route health data recorded."
            if summary["failing_routes"] > 0:
                return f"{summary['failing_routes']} failing routes remain in UI surface."
            return None

        async def probe_security_posture() -> str | None:
            blocking_findings = (
                await self.db.execute(
                    select(func.count(UISecurityPostureFinding.id)).where(
                        UISecurityPostureFinding.status.in_(["FAILED", "WARNING"])
                    )
                )
            ).scalar() or 0
            if blocking_findings > 0:
                return f"{blocking_findings} security posture findings are blocking."
            return None

        async def probe_knowledge_graph() -> str | None:
            node_count = (await self.db.execute(select(func.count(UIKnowledgeNode.id)))).scalar() or 0
            edge_count = (await self.db.execute(select(func.count(UIKnowledgeEdge.id)))).scalar() or 0
            if node_count == 0 or edge_count == 0:
                return "Knowledge graph coverage is incomplete."
            return None

        async def probe_identity_registry() -> str | None:
            active_identities = (
                await self.db.execute(
                    select(func.count(UISovereignIdentity.id)).where(UISovereignIdentity.status == "ACTIVE")
                )
            ).scalar() or 0
            if active_identities == 0:
                return "No active sovereign identities registered."
            return None

        async def probe_policy_engine() -> str | None:
            enabled_rules = (
                await self.db.execute(
                    select(func.count(UIPolicyRule.id)).where(UIPolicyRule.enabled.is_(True))
                )
            ).scalar() or 0
            if enabled_rules == 0:
                return "No enabled policy rules found."
            return None

        async def probe_finops() -> str | None:
            budget_policies = (await self.db.execute(select(func.count(UIBudgetPolicy.id)))).scalar() or 0
            cost_events = (await self.db.execute(select(func.count(UICostEvent.id)))).scalar() or 0
            if budget_policies == 0 and cost_events == 0:
                return "No FinOps evidence found."
            return None

        async def probe_resiliency_mesh() -> str | None:
            clusters = (await self.db.execute(select(func.count(UIClusterProfile.id)))).scalar() or 0
            proof_packs = (await self.db.execute(select(func.count(UIRecoveryProofPack.id)))).scalar() or 0
            if clusters == 0 and proof_packs == 0:
                return "No cluster or recovery proof evidence found."
            return None

        modules = [
            ("Health Endpoint", probe_health_endpoint),
            ("UI Repair Overview", probe_ui_repair),
            ("Security Posture", probe_security_posture),
            ("Knowledge Graph", probe_knowledge_graph),
            ("Identity Registry", probe_identity_registry),
            ("Policy Engine", probe_policy_engine),
            ("FinOps Core", probe_finops),
            ("Resiliency Mesh", probe_resiliency_mesh),
        ]

        results = [await self._build_result(module_name, probe) for module_name, probe in modules]
        passed = len([item for item in results if item.status == "PASSED"])
        failed = len(results) - passed
        logger.info("System smoke tests completed: %s passed, %s failed.", passed, failed)
        return results
