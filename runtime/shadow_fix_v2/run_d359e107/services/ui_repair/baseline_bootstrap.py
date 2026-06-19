from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIBudgetPolicy,
    UIClusterProfile,
    UIComplianceFinding,
    UIKnowledgeEdge,
    UIKnowledgeNode,
    UIPolicyRule,
    UIRecoveryProofPack,
    UISecurityRemediationPlan,
    UISovereignIdentity,
    UITenantProfile,
    RemediationStatus,
    RemediationType,
    UICostEvent,
)
from services.ui_repair.cluster_registry import ClusterRegistry
from services.ui_repair.knowledge_graph_builder import KnowledgeGraphBuilder
from services.ui_repair.recovery_proof_pack import RecoveryProofPackGenerator
from services.ui_repair.schemas import UIClusterProfileCreate, UITenantProfileCreate
from services.ui_repair.sovereign_identity_registry import SovereignIdentityRegistry
from services.ui_repair.tenant_registry import TenantRegistry


class UIRepairBaselineBootstrapper:
    """
    Seeds a minimal but evidence-backed local baseline so final smoke, audit,
    and federation/knowledge panels do not stay permanently empty in dev.
    """

    DEFAULT_TENANT_KEY = "DEFAULT_TENANT"
    DEFAULT_CLUSTER_KEY = "local-primary"
    DEFAULT_PROJECT_KEY = "UI_REPAIR"
    DEFAULT_POLICY_KEY = "BASELINE_UI_REPAIR_GOVERNANCE"
    DEFAULT_FINDING_SOURCE_ID = "BASELINE-KNOWLEDGE-FINDING"
    DEFAULT_PACK_NAME = "baseline-local-proof"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_baseline(self) -> Dict[str, bool]:
        await self._ensure_identities()
        await self._ensure_policy_rule()
        await self._ensure_finops_budget()
        await self._ensure_federation()
        await self._ensure_knowledge_sources()
        await self._ensure_recovery_proof_pack()
        knowledge_ready = await self._ensure_knowledge_graph()

        return {
            "identities_ready": await self._has_active_identities(),
            "policies_ready": await self._has_enabled_policies(),
            "finops_ready": await self._has_finops_evidence(),
            "federation_ready": await self._has_federation_baseline(),
            "knowledge_ready": knowledge_ready,
        }

    async def _ensure_identities(self) -> None:
        if await self._has_active_identities():
            return
        registry = SovereignIdentityRegistry(self.db)
        await registry.seed_identities()

    async def _ensure_policy_rule(self) -> None:
        enabled_rules = (
            await self.db.execute(
                select(func.count(UIPolicyRule.id)).where(UIPolicyRule.enabled.is_(True))
            )
        ).scalar() or 0
        if enabled_rules > 0:
            return

        self.db.add(
            UIPolicyRule(
                policy_key=self.DEFAULT_POLICY_KEY,
                scope="GLOBAL",
                project_key=self.DEFAULT_PROJECT_KEY,
                rule_type="AUTO_REPAIR",
                priority=100,
                enabled=True,
                rule_definition_json={
                    "decision": "REQUIRE_APPROVAL",
                    "actions": ["TRIGGER_REPAIR", "APPLY_PATCH"],
                    "risk_threshold": "HIGH",
                },
                description="Bootstrap baseline governance rule for local UI repair runtime.",
                created_by="system_bootstrap",
            )
        )
        await self.db.commit()

    async def _ensure_finops_budget(self) -> None:
        budget_count = (await self.db.execute(select(func.count(UIBudgetPolicy.id)))).scalar() or 0
        if budget_count == 0:
            self.db.add(
                UIBudgetPolicy(
                    project_key=self.DEFAULT_PROJECT_KEY,
                    team_key="PLATFORM",
                    daily_budget_usd=25.0,
                    weekly_budget_usd=100.0,
                    monthly_budget_usd=300.0,
                    hard_limit_usd=500.0,
                    soft_limit_percent=80.0,
                    action_on_soft_limit="NOTIFY",
                    action_on_hard_limit="BLOCK",
                )
            )
            await self.db.commit()

        cost_event_count = (await self.db.execute(select(func.count(UICostEvent.id)))).scalar() or 0
        if cost_event_count == 0:
            self.db.add(
                UICostEvent(
                    project_key=self.DEFAULT_PROJECT_KEY,
                    team_key="PLATFORM",
                    tenant_key=self.DEFAULT_TENANT_KEY,
                    cluster_key=self.DEFAULT_CLUSTER_KEY,
                    source_type="REPAIR",
                    operation_type="STAGEHAND_DIAGNOSTIC",
                    provider="OPENAI",
                    model="gpt-4o",
                    input_tokens=1500,
                    output_tokens=500,
                    estimated_cost_usd=0.045,
                )
            )
            await self.db.commit()

    async def _ensure_federation(self) -> None:
        tenant = await TenantRegistry.get_tenant(self.db, self.DEFAULT_TENANT_KEY)
        if tenant is None:
            await TenantRegistry.create_tenant(
                self.db,
                UITenantProfileCreate(
                    tenant_key=self.DEFAULT_TENANT_KEY,
                    tenant_name="Default Sovereign Tenant",
                    governance_level="STANDARD",
                    contact_info={"owner": "system_bootstrap"},
                    tenant_metadata={"bootstrap": True},
                ),
            )

        cluster = await ClusterRegistry.get_cluster(self.db, self.DEFAULT_CLUSTER_KEY)
        if cluster is None:
            await ClusterRegistry.create_cluster(
                self.db,
                UIClusterProfileCreate(
                    cluster_key=self.DEFAULT_CLUSTER_KEY,
                    cluster_name="Local Primary Cluster",
                    region="local",
                    environment="development",
                    provider="Sovereign",
                    cluster_metadata={"bootstrap": True},
                ),
            )

    async def _ensure_knowledge_sources(self) -> None:
        finding = (
            await self.db.execute(
                select(UIComplianceFinding).where(
                    UIComplianceFinding.source_id == self.DEFAULT_FINDING_SOURCE_ID
                )
            )
        ).scalar_one_or_none()

        if finding is None:
            finding = UIComplianceFinding(
                project_key=self.DEFAULT_PROJECT_KEY,
                tenant_key=self.DEFAULT_TENANT_KEY,
                cluster_key=self.DEFAULT_CLUSTER_KEY,
                source_type="BOOTSTRAP",
                source_id=self.DEFAULT_FINDING_SOURCE_ID,
                standard="INTERNAL_SECURITY",
                severity="LOW",
                finding_type="BASELINE_GRAPH_BOOTSTRAP",
                description="Baseline compliance finding used to seed knowledge graph relationships in local runtime.",
                recommendation="Keep at least one remediation-linked finding to verify knowledge graph paths.",
                status="OPEN",
            )
            self.db.add(finding)
            await self.db.commit()
            await self.db.refresh(finding)

        existing_plan = (
            await self.db.execute(
                select(UISecurityRemediationPlan).where(
                    UISecurityRemediationPlan.finding_id == finding.id
                )
            )
        ).scalar_one_or_none()

        if existing_plan is None:
            self.db.add(
                UISecurityRemediationPlan(
                    finding_id=finding.id,
                    finding_type=finding.finding_type,
                    severity=finding.severity,
                    risk_level="LOW",
                    remediation_type=RemediationType.COMPLIANCE_METADATA_FIX,
                    recommended_action="Maintain a baseline remediation link for local knowledge graph verification.",
                    affected_module="services.ui_repair.baseline_bootstrap",
                    affected_policy=self.DEFAULT_POLICY_KEY,
                    affected_route="/ui-repair",
                    requires_approval=False,
                    requires_patch=False,
                    requires_operator=False,
                    status=RemediationStatus.FIX_VERIFIED,
                )
            )
            await self.db.commit()

    async def _ensure_recovery_proof_pack(self) -> None:
        pack_count = (await self.db.execute(select(func.count(UIRecoveryProofPack.id)))).scalar() or 0
        if pack_count > 0:
            return

        now = datetime.now(timezone.utc)
        generator = RecoveryProofPackGenerator(self.db)
        await generator.generate_pack(
            self.DEFAULT_PACK_NAME,
            now - timedelta(days=7),
            now,
        )

    async def _ensure_knowledge_graph(self) -> bool:
        node_count = (await self.db.execute(select(func.count(UIKnowledgeNode.id)))).scalar() or 0
        edge_count = (await self.db.execute(select(func.count(UIKnowledgeEdge.id)))).scalar() or 0

        if node_count == 0 or edge_count == 0:
            builder = KnowledgeGraphBuilder(self.db)
            counts = await builder.rebuild_graph()
            node_count = counts["nodes"]
            edge_count = counts["edges"]

        return node_count > 0 and edge_count > 0

    async def _has_active_identities(self) -> bool:
        identity_count = (
            await self.db.execute(
                select(func.count(UISovereignIdentity.id)).where(UISovereignIdentity.status == "ACTIVE")
            )
        ).scalar() or 0
        return identity_count > 0

    async def _has_enabled_policies(self) -> bool:
        count = (
            await self.db.execute(
                select(func.count(UIPolicyRule.id)).where(UIPolicyRule.enabled.is_(True))
            )
        ).scalar() or 0
        return count > 0

    async def _has_finops_evidence(self) -> bool:
        count = (await self.db.execute(select(func.count(UIBudgetPolicy.id)))).scalar() or 0
        return count > 0

    async def _has_federation_baseline(self) -> bool:
        tenant_count = (await self.db.execute(select(func.count(UITenantProfile.id)))).scalar() or 0
        cluster_count = (await self.db.execute(select(func.count(UIClusterProfile.id)))).scalar() or 0
        return tenant_count > 0 and cluster_count > 0
