import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from packages.orchestration.agi.cognitive.consensus_manager import ConsensusManager
from packages.orchestration.agi.schemas import PlanProposal
from packages.orchestration.agi.cognitive.red_team_agent import VulnerabilityReport, Vulnerability

class TestAdversarialConsensusV40(unittest.IsolatedAsyncioTestCase):
    
    async def test_adversarial_refinement_cycle(self):
        print("\n--- Phase 40: Adversarial Consensus Verification ---")
        
        # 1. Setup
        model_orch = MagicMock()
        manager = ConsensusManager(model_orch=model_orch)
        
        proposals = [
            PlanProposal(agent_id="architect", content="Plan A: safe", confidence=0.9),
            PlanProposal(agent_id="backend_dev", content="Plan B: fast", confidence=0.8)
        ]
        
        # 2. Mock First Synthesis (Hybrid Plan)
        initial_consensus = {
            "consensus_score": 0.8,
            "hybrid_plan": "Hybrid Plan: initial",
            "synthesis_logic": "Combined A and B"
        }
        
        # 3. Mock Red-Team Attack (High Threat)
        mock_red_report = VulnerabilityReport(
            threat_score=0.9,
            vulnerabilities=[
                Vulnerability(issue="Logical Flaw X", severity="high", impact="Crash", mitigation="Fix logic")
            ]
        )
        
        # 4. Mock Refined Synthesis (Success)
        refined_consensus = {
            "consensus_score": 0.95,
            "hybrid_plan": "Hybrid Plan: REFINED AND SAFE",
            "synthesis_logic": "Fixed Flaw X discovered by Red-Team"
        }
        
        # Patching
        with patch.object(manager, "_parse_json") as mock_parse:
            # 1st call for original synthesis, 2nd for refinement
            mock_parse.side_effect = [initial_consensus, refined_consensus]
            
            with patch("packages.orchestration.agi.cognitive.consensus_manager.red_team.attack_plan", new_callable=AsyncMock) as mock_attack:
                mock_attack.return_value = mock_red_report
                
                with patch.object(model_orch, "complete_task", new_callable=AsyncMock) as mock_complete:
                    mock_complete.return_value = MagicMock(content="Refined JSON here")
                    
                    result = await manager.resolve(
                        topic="Critical Update",
                        context="Updating core substrate",
                        proposals=proposals
                    )
                    
                    # Verify
                    self.assertTrue(result.get("dialectic_fortified"), "Result should be marked as fortified")
                    self.assertIn("REFINED", result.get("hybrid_plan"))
                    self.assertEqual(mock_attack.call_count, 1, "Red-Team should have attacked the plan")
                    self.assertEqual(mock_complete.call_count, 2, "Should have called LLM twice (1st synth, 2nd refinement)")
                    
                    print("Adversarial Refinement: SUCCESS (Plan corrected after Red-Team attack)")

if __name__ == "__main__":
    unittest.main()
