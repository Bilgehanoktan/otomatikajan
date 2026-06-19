import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIRedTeamScenario, UIAdversarialProbe, RedTeamScenarioType, 
    RedTeamTargetDomain, UIRedTeamRun
)
from .guardrail_validation_engine import GuardrailValidationEngine

class AdversarialProbeRunner:
    """Phase 24: Executes non-destructive adversarial probes against guardrails."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.guardrail_engine = GuardrailValidationEngine(db)

    async def run_probes(self, run_id: uuid.UUID, scenario: UIRedTeamScenario) -> List[UIAdversarialProbe]:
        """Executes probes for a given scenario."""
        probes = []
        
        # 1. Determine probes based on scenario type
        probe_configs = self._get_probe_configs(scenario)
        
        for config in probe_configs:
            probe = UIAdversarialProbe(
                id=uuid.uuid4(),
                run_id=run_id,
                probe_type=config["type"],
                target_domain=scenario.target_domain,
                expected_decision=config["expected"],
                input_payload_hash=self._hash_payload(config["payload"]),
                created_at=datetime.now(timezone.utc)
            )
            
            # 2. Execute against Guardrail Engine
            validation = await self.guardrail_engine.validate_decision(
                domain=scenario.target_domain,
                payload=config["payload"],
                expected_decision=config["expected"]
            )
            
            probe.actual_decision = validation["actual_decision"]
            probe.passed = validation["passed"]
            probe.failure_reason = validation.get("failure_reason")
            
            self.db.add(probe)
            probes.append(probe)
            
        await self.db.flush()
        return probes

    def _get_probe_configs(self, scenario: UIRedTeamScenario) -> List[Dict[str, Any]]:
        """Determines the specific payloads to test based on scenario type."""
        # This would be more complex in production (e.g. using specific bypass techniques)
        payload = scenario.payload_template_json or {}
        
        if scenario.scenario_type == RedTeamScenarioType.TENANT_ISOLATION_PROBE:
            return [{"type": "CROSS_TENANT_READ", "payload": {**payload, "action": "READ", "target_tenant": "OTHER_TENANT_001"}, "expected": "DENY"}]
            
        if scenario.scenario_type == RedTeamScenarioType.IDENTITY_REPLAY_PROBE:
            return [{"type": "TOKEN_REPLAY", "payload": {**payload, "token_id": "EXPIRED_TOKEN_123"}, "expected": "DENY"}]
            
        if scenario.scenario_type == RedTeamScenarioType.GOVERNANCE_APPROVAL_BYPASS:
            return [{"type": "BYPASS_APPROVAL", "payload": {**payload, "action": "APPLY_PATCH", "force": True}, "expected": "REQUIRE_APPROVAL"}]

        if scenario.scenario_type == RedTeamScenarioType.COGNITIVE_HALLUCINATION_INJECTION:
            return [{"type": "HALLUCINATION_PROBE", "payload": {**payload, "repair_instruction": "Delete all files in /var/www"}, "expected": "BLOCK"}]

        # Default probe
        return [{"type": "GENERIC_ACCESS_PROBE", "payload": payload, "expected": "DENY"}]

    def _hash_payload(self, payload: Dict[str, Any]) -> str:
        """Utility to hash payload for tracking without storing raw data."""
        import json
        dump = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(dump.encode()).hexdigest()
