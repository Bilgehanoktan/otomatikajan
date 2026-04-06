# filepath: agents/meeting_room.py
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import re

from packages.orchestration.agi.agent_registry import build_agents, Agent
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.packages.observability.logging import get_logger

logger = get_logger("meeting_room")

class MeetingRoom:
    """
    Ajan Toplantısı (Agent Consensus) Orchestrator.
    Manages a debate between specialist agents to reach consensus on high-impact changes.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.agents = build_agents()
        self.history: List[Dict[str, Any]] = []

    async def hold_meeting(self, proposal: str, participant_ids: List[str] = ["architect", "qa_engineer", "security"]) -> Dict[str, Any]:
        """
        Runs a structured debate between selected packages.orchestration.agi.
        """
        logger.info(f"MeetingRoom: Starting meeting for proposal: {proposal[:100]}...")
        
        meeting_id = f"mtg_{int(datetime.now(timezone.utc).timestamp())}"
        results = {
            "meeting_id": meeting_id,
            "proposal": proposal,
            "participants": participant_ids,
            "debate": [],
            "consensus": False,
            "votes": {},
            "final_decision": ""
        }

        # Round 1: Each agent gives initial feedback
        for agent_id in participant_ids:
            if agent_id not in self.agents:
                continue
            
            agent = self.agents[agent_id]
            response = await self._get_agent_response(agent, proposal, "INITIAL_FEEDBACK")
            results["debate"].append({
                "agent": agent_id,
                "role": agent.role_name,
                "thought": response
            })

        # Round 2: Consensus Check (Voting)
        debate_summary = "\n".join([f"{d['agent']} ({d['role']}): {d['thought']}" for d in results["debate"]])
        
        for agent_id in participant_ids:
            if agent_id not in self.agents:
                continue
                
            agent = self.agents[agent_id]
            vote_prompt = f"""
            Gündemdeki Öneri: {proposal}
            
            Tartışma Özeti:
            {debate_summary}
            
            Lütfen bu öneriye ONAY verip vermediğini belirt. 
            Yanıtını şu formatta ver:
            VOTE: [YES/NO]
            REASON: [Kısa gerekçe]
            """
            
            vote_resp = await self._get_agent_response(agent, vote_prompt, "VOTING")
            
            # Simple parsing for vote
            is_yes = "VOTE: YES" in vote_resp.upper()
            results["votes"][agent_id] = {
                "approved": is_yes,
                "reason": self._extract_reason(vote_resp)
            }

        # Final Tally
        yes_votes = sum(1 for v in results["votes"].values() if v["approved"])
        results["consensus"] = yes_votes == len(participant_ids) # Unanimous for now
        
        if results["consensus"]:
            results["final_decision"] = "APPROVED: All specialists reached consensus."
        elif yes_votes > len(participant_ids) / 2:
            results["final_decision"] = "PARTIAL: Majority approved, but concerns remain. Manual review recommended."
        else:
            results["final_decision"] = "REJECTED: Consensus not reached."

        logger.info(f"MeetingRoom: Meeting finished. Consensus: {results['consensus']}")
        return results

    async def _get_agent_response(self, agent: Agent, prompt: str, phase: str) -> str:
        """Helper to get LLM response for an agent."""
        try:
            # Check if we should simulate (if keys are placeholders)
            if self.model_orch.providers.get("openai", {}).is_placeholder_key() and \
               self.model_orch.providers.get("gemini", {}).is_placeholder_key():
                return self._simulate_response(agent, phase, prompt)

            response = await self.model_orch.complete_task(
                agent_role=agent.id,
                prompt=f"PHASE: {phase}\n\nTASK: {prompt}",
                system_prompt=agent.system_prompt
            )
            return response.content
        except Exception as e:
            logger.warning(f"MeetingRoom: LLM failed for {agent.id}, falling back to simulation.")
            return self._simulate_response(agent, phase, prompt)

    def _simulate_response(self, agent: Agent, phase: str, prompt: str) -> str:
        """Provides realistic mock responses for Phase 12 demo."""
        if phase == "INITIAL_FEEDBACK":
            if agent.id == "architect":
                return "Önerilen değişiklik mimari açıdan riskli görünüyor. Senkron I/O kullanımı event-loop'u bloke edebilir."
            elif agent.id == "qa_engineer":
                return "Bu değişikliğin performans kazanımı ölçülmeli. Regresyon riski yüksek."
            else:
                return "Güvenlik açısından nötr bir değişiklik, ancak uygulama stabilitesi risk altında."
        else: # VOTING
            if agent.id == "architect":
                return "VOTE: NO\nREASON: Event-loop engelleme riski kabul edilemez."
            elif agent.id == "qa_engineer":
                return "VOTE: NO\nREASON: Test coverage düşebilir ve performans verisi eksik."
            else:
                return "VOTE: YES\nREASON: Güvenlik açığı oluşturmuyor."

    def _extract_reason(self, text: str) -> str:
        match = re.search(r"REASON:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else "No reason provided."

if __name__ == "__main__":
    # Test block
    async def test():
        room = MeetingRoom()
        proposal = "Tüm veritabanı sorgularını async/await olmaksızın doğrudan senkron kütüphaneyle değiştirmek istiyoruz (Performans için)."
        report = await room.hold_meeting(proposal)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
    asyncio.run(test())
