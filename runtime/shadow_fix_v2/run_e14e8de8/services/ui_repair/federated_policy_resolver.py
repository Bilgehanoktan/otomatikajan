import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import UIPolicyRule, UITenantProjectBinding
from services.ui_repair.schemas import PolicyDecision, PolicyScope
from services.ui_repair.policy_as_code_engine import PolicyAsCodeEngine

logger = logging.getLogger(__name__)

class FederatedPolicyResolver:
    """
    Resolves policies across the federated hierarchy: Global -> Tenant -> Cluster -> Project.
    Implements the 'Most Restrictive Wins' rule.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_effective_engine(self, project_key: str) -> PolicyAsCodeEngine:
        """
        Gathers all applicable rules for a project from the federation hierarchy
        and returns a PolicyAsCodeEngine initialized with them.
        """
        # 1. Get Tenant and Cluster bindings for this project
        stmt = select(UITenantProjectBinding).where(UITenantProjectBinding.project_key == project_key)
        binding = (await self.db.execute(stmt)).scalar_one_or_none()
        
        tenant_key = binding.tenant_key if binding else None
        cluster_key = binding.cluster_key if binding else None

        # 2. Gather rules from all levels
        queries = []
        
        # Level 1: Global
        queries.append(select(UIPolicyRule).where(
            (UIPolicyRule.enabled == True) & 
            (UIPolicyRule.scope == "GLOBAL")
        ))
        
        # Level 2: Tenant
        if tenant_key:
            queries.append(select(UIPolicyRule).where(
                (UIPolicyRule.enabled == True) & 
                (UIPolicyRule.scope == "TENANT") & 
                (UIPolicyRule.tenant_key == tenant_key)
            ))
            
        # Level 3: Cluster
        if cluster_key:
            queries.append(select(UIPolicyRule).where(
                (UIPolicyRule.enabled == True) & 
                (UIPolicyRule.scope == "CLUSTER") & 
                (UIPolicyRule.cluster_key == cluster_key)
            ))
            
        # Level 4: Project
        queries.append(select(UIPolicyRule).where(
            (UIPolicyRule.enabled == True) & 
            (UIPolicyRule.scope == "PROJECT") & 
            (UIPolicyRule.project_key == project_key)
        ))

        from sqlalchemy import union
        rules_query = union(*queries)

        # Ensure we get ORM objects back
        stmt = select(UIPolicyRule).from_statement(rules_query)
        result = await self.db.execute(stmt)
        rules = list(result.scalars().all())
        
        # The PolicyAsCodeEngine already sorts by scope and priority.
        # We need to ensure that 'Most Restrictive Wins' is handled during evaluation.
        # The engine's _is_more_restrictive method already handles this hierarchy:
        # DENY > REQUIRE_APPROVAL > ALLOW.
        
        return PolicyAsCodeEngine(rules)

    async def evaluate_federated_action(self, action_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates an action against the full federated policy stack."""
        project_key = context.get("project_key", "GLOBAL")
        engine = await self.get_effective_engine(project_key)
        
        # Ensure context has tenant/cluster info for rule matching
        stmt = select(UITenantProjectBinding).where(UITenantProjectBinding.project_key == project_key)
        binding = (await self.db.execute(stmt)).scalar_one_or_none()
        if binding:
            context["tenant_key"] = binding.tenant_key
            context["cluster_key"] = binding.cluster_key
            
        return engine.evaluate(action_type, context)
