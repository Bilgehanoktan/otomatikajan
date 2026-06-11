import hashlib
import json
from typing import Dict, Any, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.repair_models import AgentCapabilityModel, AgentArtifactPromotionModel

class AgentPolicySimulator:
    """
    Read-only dry-run policy rules and risk score preview generator.
    Enforces risk score levels:
      0-24   -> LOW
      25-49  -> MEDIUM
      50-74  -> HIGH
      75-100 -> CRITICAL
    """

    @classmethod
    def calculate_risk_score(
        cls,
        agent_enabled: bool,
        sandbox_mode: str,
        path_check: Tuple[bool, str],
        cost: float,
        cost_limit: float,
        network_request: bool,
        network_allowed: str,
        verification_score: float = 1.0,
        hash_mismatch: bool = False
    ) -> Tuple[float, List[str]]:
        """Computes a risk score from 0.0 to 100.0 and gathers reasoning reasons."""
        score = 0.0
        reasons = []

        # 1. Agent enabled state risk
        if not agent_enabled:
            score += 25.0
            reasons.append("Agent capability is disabled in the registry.")

        # 2. Sandbox mode risk
        if sandbox_mode == "direct-write":
            score += 40.0
            reasons.append("Agent sandbox is configured in direct-write mode.")
        elif sandbox_mode == "workspace-write":
            score += 15.0
            reasons.append("Agent sandbox is configured in workspace-write mode.")
        else:
            score += 5.0  # read-only

        # 3. Path risk
        path_ok, path_msg = path_check
        if not path_ok:
            score += 35.0
            reasons.append(f"Target path policy check failed: {path_msg}")

        # 4. Cost risk
        if cost > cost_limit:
            score += 20.0
            reasons.append(f"Requested cost (${cost}) exceeds limit (${cost_limit}).")

        # 5. Network risk
        if network_request:
            if network_allowed == "disabled":
                score += 30.0
                reasons.append("Network requests are simulated but network policy is disabled.")
            elif network_allowed == "restricted":
                score += 10.0
                reasons.append("Network requests are simulated under restricted domain filters.")

        # 6. Verification and Integrity risk (used for promotions)
        if verification_score < 1.0:
            score += 25.0
            reasons.append(f"Static verifier did not pass perfectly (Score: {verification_score}).")

        if hash_mismatch:
            score += 50.0
            reasons.append("Integrity hash mismatch detected across lifecycle states.")

        return min(100.0, score), reasons

    @classmethod
    def get_risk_level(cls, score: float) -> str:
        if score < 25.0:
            return "LOW"
        elif score < 50.0:
            return "MEDIUM"
        elif score < 75.0:
            return "HIGH"
        else:
            return "CRITICAL"

    @classmethod
    def get_decision(cls, risk_level: str) -> str:
        if risk_level in ["LOW", "MEDIUM"]:
            return "ALLOW"
        elif risk_level == "HIGH":
            return "HUMAN_GATE_REQUIRED"
        else:
            return "BLOCK"

    @classmethod
    def compute_result_hash(cls, decision: str, risk_level: str, score: float, reasons: List[str]) -> str:
        """Helper to generate a hash of the simulation result to seal the state."""
        payload = {
            "decision": decision,
            "risk_level": risk_level,
            "risk_score": round(score, 2),
            "reasons": sorted(reasons)
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    async def simulate_agent_run(
        cls,
        db: AsyncSession,
        agent_key: str,
        action_type: str,
        target_paths: List[str],
        cost: float,
        network_request: bool
    ) -> Dict[str, Any]:
        """Runs a read-only policy simulation for starting an agent execution run."""
        stmt = select(AgentCapabilityModel).where(AgentCapabilityModel.agent_key == agent_key)
        res = await db.execute(stmt)
        cap = res.scalars().first()
        if not cap:
            return {
                "decision": "BLOCK",
                "risk_level": "CRITICAL",
                "risk_score": 100.0,
                "reasons": [f"Agent key '{agent_key}' not found in registry."],
                "required_permissions": [],
                "blocked_actions": ["execute_run"],
                "ledger_context": {}
            }

        # Validate target paths
        path_ok = True
        path_msg = ""
        from services.repair.external_agents.agent_promotion_gate import AgentPromotionGate
        for p in target_paths:
            ok, msg = AgentPromotionGate.validate_target_path(p)
            if not ok:
                path_ok = False
                path_msg = msg
                break

        score, reasons = cls.calculate_risk_score(
            agent_enabled=cap.enabled,
            sandbox_mode=cap.sandbox_mode,
            path_check=(path_ok, path_msg),
            cost=cost,
            cost_limit=cap.max_cost_limit,
            network_request=network_request,
            network_allowed=cap.network_policy
        )

        risk_level = cls.get_risk_level(score)
        decision = cls.get_decision(risk_level)

        # Enforce hard block on disabled agent or traversal
        if not cap.enabled or not path_ok:
            decision = "BLOCK"

        result_hash = cls.compute_result_hash(decision, risk_level, score, reasons)

        return {
            "decision": decision,
            "risk_level": risk_level,
            "risk_score": score,
            "reasons": reasons,
            "required_permissions": ["agents.manage"] if decision == "HUMAN_GATE_REQUIRED" else [],
            "blocked_actions": ["execute_run"] if decision == "BLOCK" else [],
            "ledger_context": {
                "agent_key": agent_key,
                "action_type": action_type,
                "risk_level": risk_level,
                "risk_score": score
            },
            "simulation_result_hash": result_hash
        }

    @classmethod
    async def simulate_promotion(
        cls,
        db: AsyncSession,
        promotion_id: str
    ) -> Dict[str, Any]:
        """Runs a read-only policy simulation for executing a promotion request."""
        stmt = select(AgentArtifactPromotionModel).where(AgentArtifactPromotionModel.promotion_id == promotion_id)
        res = await db.execute(stmt)
        promo = res.scalars().first()
        if not promo:
            return {
                "decision": "BLOCK",
                "risk_level": "CRITICAL",
                "risk_score": 100.0,
                "reasons": [f"Promotion request '{promotion_id}' not found."],
                "required_permissions": [],
                "blocked_actions": ["execute_promotion"],
                "ledger_context": {}
            }

        # Read sandbox mode from current agent run config
        from libs.db.models.repair_models import AgentRunModel
        stmt_run = select(AgentRunModel).where(AgentRunModel.run_id == promo.run_id)
        res_run = await db.execute(stmt_run)
        run_rec = res_run.scalars().first()
        sandbox_mode = run_rec.sandbox_mode if run_rec else "workspace-write"
        cost = run_rec.cost if run_rec else 0.0

        # Target path checks
        from services.repair.external_agents.agent_promotion_gate import AgentPromotionGate
        path_ok, path_msg = AgentPromotionGate.validate_target_path(promo.target_repo_path)

        # Check hash integrity
        hash_mismatch = False
        if promo.verified_artifact_hash and promo.verified_artifact_hash != promo.artifact_hash:
            hash_mismatch = True
        if promo.approved_artifact_hash and promo.approved_artifact_hash != promo.artifact_hash:
            hash_mismatch = True

        score, reasons = cls.calculate_risk_score(
            agent_enabled=True,  # Assuming verification stage capability check passed
            sandbox_mode=sandbox_mode,
            path_check=(path_ok, path_msg),
            cost=cost,
            cost_limit=10.0,  # general threshold
            network_request=False,
            network_allowed="disabled",
            verification_score=promo.verification_score,
            hash_mismatch=hash_mismatch
        )

        # Add promotion specific state reasons
        if promo.status == "REJECTED":
            score += 60.0
            reasons.append("Promotion request is already rejected.")
        elif promo.status == "PROMOTED":
            score += 50.0
            reasons.append("Promotion request has already been completed.")

        risk_level = cls.get_risk_level(score)
        decision = cls.get_decision(risk_level)

        if not path_ok or hash_mismatch or promo.status in ["REJECTED", "PROMOTED", "VERIFICATION_FAILED"]:
            decision = "BLOCK"

        result_hash = cls.compute_result_hash(decision, risk_level, score, reasons)

        return {
            "decision": decision,
            "risk_level": risk_level,
            "risk_score": score,
            "reasons": reasons,
            "required_permissions": ["agents.promotions.execute"] if decision == "HUMAN_GATE_REQUIRED" else [],
            "blocked_actions": ["execute_promotion"] if decision == "BLOCK" else [],
            "ledger_context": {
                "promotion_id": promotion_id,
                "run_id": promo.run_id,
                "target_repo_path": promo.target_repo_path,
                "verification_score": promo.verification_score,
                "status": promo.status
            },
            "simulation_result_hash": result_hash
        }
