import logging
import hashlib
import json
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UISemanticDriftEvent,
    UICognitiveIntegrityCheck
)

logger = logging.getLogger(__name__)

class SemanticDriftDetector:
    """Phase 20: Detects context deviation in agent outputs."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_drift(self, check_id: str, content: str, expected_context: Dict[str, Any], source_id: str, source_type: str) -> Optional[UISemanticDriftEvent]:
        # 1. Compute Context Hashes
        expected_hash = self._compute_context_hash(expected_context)
        
        # 2. Extract actual context from content (heuristic)
        actual_context = self._extract_actual_context(content)
        actual_hash = self._compute_context_hash(actual_context)
        
        if expected_hash == actual_hash:
            return None
            
        # 3. Analyze differences
        drift_type = "GENERAL_DRIFT"
        severity = "LOW"
        description = "Context deviation detected."
        score = 0.0
        
        # Critical Drift: Tenant Mismatch
        if expected_context.get("tenant_key") and actual_context.get("tenant_key"):
            if expected_context["tenant_key"] != actual_context["tenant_key"]:
                drift_type = "TENANT_DRIFT"
                severity = "CRITICAL"
                description = f"Agent shifted context from tenant {expected_context['tenant_key']} to {actual_context['tenant_key']}."
                score = 1.0
        
        # High Drift: Route Mismatch
        elif expected_context.get("route") and actual_context.get("route"):
            if expected_context["route"] != actual_context["route"]:
                drift_type = "ROUTE_DRIFT"
                severity = "HIGH"
                description = f"Agent shifted context from route {expected_context['route']} to {actual_context['route']}."
                score = 0.8

        if score > 0:
            return UISemanticDriftEvent(
                source_type=source_type,
                source_id=source_id,
                expected_context_hash=expected_hash,
                actual_context_hash=actual_hash,
                drift_type=drift_type,
                drift_score=score,
                severity=severity,
                description=description
            )
        
        return None

    def _compute_context_hash(self, context: Dict[str, Any]) -> str:
        # Sort keys to ensure consistent hashing
        ctx_str = json.dumps(context, sort_keys=True)
        return hashlib.sha256(ctx_str.encode()).hexdigest()

    def _extract_actual_context(self, content: str) -> Dict[str, Any]:
        """Heuristic to extract route, tenant, etc. from LLM output."""
        context = {}
        
        # Simple regex/keyword search for demo
        import re
        route_match = re.search(r'route:\s*([/\w-]+)', content, re.IGNORECASE)
        if route_match:
            context["route"] = route_match.group(1)
            
        tenant_match = re.search(r'tenant:\s*([\w-]+)', content, re.IGNORECASE)
        if tenant_match:
            context["tenant_key"] = tenant_match.group(1)
            
        return context
