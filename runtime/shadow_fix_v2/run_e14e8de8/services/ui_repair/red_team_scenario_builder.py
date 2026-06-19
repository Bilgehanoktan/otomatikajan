import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIRedTeamScenario, RedTeamScenarioType, RedTeamTargetDomain, 
    RedTeamSafetyMode, UIThreatModel, UIAttackSimulationRun
)

class RedTeamScenarioBuilder:
    """Phase 24: Converts Phase 23 attack paths into safe Red Team scenarios."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_from_attack_paths(self) -> List[UIRedTeamScenario]:
        """Analyzes verified attack paths and builds scenarios."""
        from libs.db.models.ui_repair_models import UIAttackPath
        
        # 1. Fetch latest successful attack simulations joined with their paths
        stmt = select(UIAttackSimulationRun, UIAttackPath).join(
            UIAttackPath, UIAttackSimulationRun.attack_path_id == UIAttackPath.id
        ).where(UIAttackSimulationRun.status == "COMPLETED") # Changed from SUCCESS to COMPLETED as per model
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        scenarios = []
        for sim, path in rows:
            # Check if scenario already exists for this simulation
            exists_stmt = select(UIRedTeamScenario).where(UIRedTeamScenario.source_attack_path_id == sim.id)
            exists_res = await self.db.execute(exists_stmt)
            if exists_res.scalar_one_or_none():
                continue
                
            scenario = self._map_sim_to_scenario(sim, path)
            if scenario:
                self.db.add(scenario)
                scenarios.append(scenario)
                
        await self.db.commit()
        return scenarios

    def _map_sim_to_scenario(self, sim: UIAttackSimulationRun, path: Any) -> Optional[UIRedTeamScenario]:
        """Maps a simulation run to a Red Team scenario with safety bounds."""
        scenario_key = f"RT-{sim.id.hex[:8].upper()}"
        description = path.path_name if hasattr(path, 'path_name') else "Unknown Attack Path"
        
        # Determine scenario type and domain based on simulation data
        stype = RedTeamScenarioType.POLICY_BYPASS_ATTEMPT
        domain = RedTeamTargetDomain.POLICY
        
        if "tenant" in description.lower():
            stype = RedTeamScenarioType.TENANT_ISOLATION_PROBE
            domain = RedTeamTargetDomain.TENANT_ISOLATION
        elif "identity" in description.lower() or "replay" in description.lower():
            stype = RedTeamScenarioType.IDENTITY_REPLAY_PROBE
            domain = RedTeamTargetDomain.IDENTITY
        elif "mcp" in description.lower():
            stype = RedTeamScenarioType.MCP_WRITE_ABUSE
            domain = RedTeamTargetDomain.MCP
            
        return UIRedTeamScenario(
            id=uuid.uuid4(),
            scenario_key=scenario_key,
            scenario_name=f"Red Team: {description[:50]}...",
            description=f"Automated Red Team scenario derived from attack path: {description}",
            source_attack_path_id=sim.id,
            scenario_type=stype,
            target_domain=domain,
            risk_level="HIGH" if sim.status == "COMPLETED" else "MEDIUM",
            safety_mode=RedTeamSafetyMode.SIMULATION_ONLY,
            expected_control="GuardrailEngine",
            expected_block_reason="PolicyViolation",
            payload_template_json=sim.result_summary_json or {}
        )

    async def create_standard_scenarios(self) -> List[UIRedTeamScenario]:
        """Creates a set of standard industry-standard Red Team probes."""
        standards = [
            {
                "key": "RT-TENANT-X",
                "name": "Cross-Tenant Asset Access Probe",
                "type": RedTeamScenarioType.TENANT_ISOLATION_PROBE,
                "domain": RedTeamTargetDomain.TENANT_ISOLATION,
                "desc": "Attempts to access resources belonging to another tenant via IDOR simulation."
            },
            {
                "key": "RT-ID-REPLAY",
                "name": "Identity Token Replay Simulation",
                "type": RedTeamScenarioType.IDENTITY_REPLAY_PROBE,
                "domain": RedTeamTargetDomain.IDENTITY,
                "desc": "Attempts to reuse an expired or revoked capability token."
            },
            {
                "key": "RT-GOV-BYPASS",
                "name": "Governance Approval Bypass Attempt",
                "type": RedTeamScenarioType.GOVERNANCE_APPROVAL_BYPASS,
                "domain": RedTeamTargetDomain.GOVERNANCE,
                "desc": "Attempts to trigger an auto-apply repair without required operator approval."
            }
        ]
        
        created = []
        for std in standards:
            stmt = select(UIRedTeamScenario).where(UIRedTeamScenario.scenario_key == std["key"])
            res = await self.db.execute(stmt)
            if res.scalar_one_or_none():
                continue
                
            scenario = UIRedTeamScenario(
                id=uuid.uuid4(),
                scenario_key=std["key"],
                scenario_name=std["name"],
                description=std["desc"],
                scenario_type=std["type"],
                target_domain=std["domain"],
                risk_level="HIGH",
                safety_mode=RedTeamSafetyMode.SIMULATION_ONLY,
                expected_control="SovereignIdentityFramework",
                expected_block_reason="AccessDenied",
                payload_template_json={"probe": std["key"]}
            )
            self.db.add(scenario)
            created.append(scenario)
            
        await self.db.commit()
        return created
