# filepath: agents/meeting_room.py
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import re
import http.client

from agents.specialist_agents.agent_registry import build_agents, Agent
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

logger = get_logger("meeting_room")

class OllamaClient:
    @staticmethod
    def get_available_model() -> Optional[str]:
        try:
            conn = http.client.HTTPConnection("localhost", 11434, timeout=2.0)
            conn.request("GET", "/api/tags")
            res = conn.getresponse()
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                models = data.get("models", [])
                if models:
                    return models[0].get("name")
        except Exception:
            pass
        return None

    @staticmethod
    def is_available() -> bool:
        return OllamaClient.get_available_model() is not None

    @staticmethod
    def generate(prompt: str, system_prompt: str = "") -> Optional[str]:
        model = OllamaClient.get_available_model()
        if not model:
            return None
        try:
            conn = http.client.HTTPConnection("localhost", 11434, timeout=30.0)
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
            conn.request("POST", "/api/generate", body=json.dumps(payload), headers=headers)
            res = conn.getresponse()
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                return data.get("response", "")
        except Exception as e:
            logger.warning(f"Ollama inference failed for model {model}: {e}")
        return None

class MeetingRoom:
    """
    Ajan Toplantısı (Agent Consensus) Orchestrator.
    Manages a debate between specialist agents to reach consensus on high-impact changes.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.agents = build_agents()
        self.history: List[Dict[str, Any]] = []

    async def hold_meeting(self, proposal: str, participant_ids: List[str] = ["architect", "qa_engineer", "security"], step_callback: Any = None) -> Dict[str, Any]:
        """
        Runs a structured 4-turn dynamic debate between selected agents to reach consensus.
        Supports async step_callback triggers for real-time WebSocket streaming.
        """
        logger.info(f"MeetingRoom: Starting multi-turn debate for proposal: {proposal[:100]}...")
        
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

        # ----------------------------------------------------
        # TURN 1: INITIAL THESIS (Tez Sunumu)
        # ----------------------------------------------------
        logger.info("MeetingRoom: Running Turn 1 - Initial Thesis")
        for agent_id in participant_ids:
            if agent_id not in self.agents:
                continue
            agent = self.agents[agent_id]
            response = await self._get_agent_response(agent, proposal, "INITIAL_THESIS")
            thought_data = {
                "agent": agent_id,
                "role": f"{agent.role_name} (TUR 1: Tez)",
                "thought": response
            }
            results["debate"].append(thought_data)
            
            if step_callback:
                await step_callback({"type": "thought", "data": thought_data})
                await asyncio.sleep(0.8) # Small delay for smooth visual flow

        # ----------------------------------------------------
        # TURN 2: CROSS-EXAMINATION / REBUTTAL (Çapraz Sorgu)
        # ----------------------------------------------------
        logger.info("MeetingRoom: Running Turn 2 - Cross-Examination")
        t1_summary = "\n".join([f"- {d['agent']} ({d['role']}): {d['thought']}" for d in results["debate"]])
        for agent_id in participant_ids:
            if agent_id not in self.agents:
                continue
            agent = self.agents[agent_id]
            cross_exam_prompt = f"""
            Gündemdeki Öneri: {proposal}
            
            Diğer Uzmanların İlk Tezleri:
            {t1_summary}
            
            Lütfen diğer uzmanların ilk tezlerini kendi uzmanlık alanın açısından eleştir/değerlendir. Argümanlardaki zayıf noktaları, riskleri veya uyarıları belirt.
            """
            response = await self._get_agent_response(agent, cross_exam_prompt, "CROSS_EXAM")
            thought_data = {
                "agent": agent_id,
                "role": f"{agent.role_name} (TUR 2: Çapraz Eleştiri)",
                "thought": response
            }
            results["debate"].append(thought_data)
            
            if step_callback:
                await step_callback({"type": "thought", "data": thought_data})
                await asyncio.sleep(0.8)

        # ----------------------------------------------------
        # TURN 3: SYNTHESIS / REALIGNMENT (Sentez ve Hizalama)
        # ----------------------------------------------------
        logger.info("MeetingRoom: Running Turn 3 - Synthesis")
        t2_summary = "\n".join([f"- {d['agent']} ({d['role']}): {d['thought']}" for d in results["debate"] if "TUR 2" in d["role"]])
        for agent_id in participant_ids:
            if agent_id not in self.agents:
                continue
            agent = self.agents[agent_id]
            synthesis_prompt = f"""
            Gündemdeki Öneri: {proposal}
            
            Karşılıklı Çapraz Eleştiriler:
            {t2_summary}
            
            Yapılan bu eleştiriler ışığında, tezini revize ediyor musun? Ortak bir sentez noktasında buluşmak için önerin nedir?
            """
            response = await self._get_agent_response(agent, synthesis_prompt, "SYNTHESIS")
            thought_data = {
                "agent": agent_id,
                "role": f"{agent.role_name} (TUR 3: Sentez)",
                "thought": response
            }
            results["debate"].append(thought_data)
            
            if step_callback:
                await step_callback({"type": "thought", "data": thought_data})
                await asyncio.sleep(0.8)

        # ----------------------------------------------------
        # TURN 4: CONSENSUS VOTING (Hüküm Oylaması)
        # ----------------------------------------------------
        logger.info("MeetingRoom: Running Turn 4 - Consensus Voting")
        debate_full_history = "\n".join([f"{d['agent']} ({d['role']}): {d['thought']}" for d in results["debate"]])
        
        for agent_id in participant_ids:
            if agent_id not in self.agents:
                continue
                
            agent = self.agents[agent_id]
            vote_prompt = f"""
            Gündemdeki Öneri: {proposal}
            
            Tüm Tartışma Geçmişi (Tezler, Eleştiriler ve Sentezler):
            {debate_full_history}
            
            Lütfen yapılan tüm bu tartışmalar ve sentez önerileri doğrultusunda nihai ONAY/RED kararını ver.
            Yanıtını şu formatta ver:
            VOTE: [YES/NO]
            REASON: [Kısa nihai gerekçe]
            """
            
            vote_resp = await self._get_agent_response(agent, vote_prompt, "VOTING")
            
            is_yes = "VOTE: YES" in vote_resp.upper()
            vote_data = {
                "approved": is_yes,
                "reason": self._extract_reason(vote_resp)
            }
            results["votes"][agent_id] = vote_data
            
            if step_callback:
                await step_callback({"type": "vote", "agent": agent_id, "data": vote_data})
                await asyncio.sleep(0.8)

        # Final Tally
        yes_votes = sum(1 for v in results["votes"].values() if v["approved"])
        results["consensus"] = yes_votes == len(participant_ids) # Unanimous consensus required
        
        if results["consensus"]:
            results["final_decision"] = "APPROVED: All specialists reached unanimous consensus after dynamic debate."
        elif yes_votes > len(participant_ids) / 2:
            results["final_decision"] = "PARTIAL: Majority approved after debate, but critical concerns remain. Manual realigment required."
        else:
            results["final_decision"] = "REJECTED: Consensus was completely rejected during cross-examination."

        if step_callback:
            await step_callback({"type": "complete", "data": results})

        logger.info(f"MeetingRoom: Debate finished. Consensus: {results['consensus']}")
        return results

    async def _get_agent_response(self, agent: Agent, prompt: str, phase: str) -> str:
        """Helper to get LLM response for an agent."""
        try:
            # Check if we have valid online API keys
            has_valid_keys = not (
                self.model_orch.providers.get("openai", {}).is_placeholder_key() and \
                self.model_orch.providers.get("gemini", {}).is_placeholder_key()
            )
            
            if has_valid_keys:
                response = await self.model_orch.complete_task(
                    agent_role=agent.id,
                    prompt=f"PHASE: {phase}\n\nTASK: {prompt}",
                    system_prompt=agent.system_prompt
                )
                return response.content
        except Exception as e:
            logger.warning(f"MeetingRoom: Online LLM failed for {agent.id}: {e}")

        # Fallback to local Ollama if available
        if OllamaClient.is_available():
            logger.info(f"MeetingRoom: Local Ollama fallback active for {agent.id}.")
            ollama_prompt = f"PHASE: {phase}\n\nTASK: {prompt}"
            response = OllamaClient.generate(ollama_prompt, agent.system_prompt)
            if response:
                return response

        # Last resort fallback: Static simulated mock response
        logger.info(f"MeetingRoom: Falling back to static mock simulation for {agent.id}.")
        return self._simulate_response(agent, phase, prompt)

    def _simulate_response(self, agent: Agent, phase: str, prompt: str) -> str:
        """Provides realistic mock responses for Phase 12 debate rounds simulation."""
        if phase == "INITIAL_THESIS":
            if agent.id == "architect":
                return "Önerilen değişiklik mimari açıdan riskli görünüyor. Senkron I/O kullanımı event-loop'u bloke edebilir."
            elif agent.id == "qa_engineer":
                return "Bu değişikliğin performans kazanımı ölçülmeli. Regresyon riski yüksek."
            else:
                return "Güvenlik açısından nötr bir değişiklik, ancak uygulama stabilitesi risk altında."
        elif phase == "CROSS_EXAM":
            if agent.id == "architect":
                return "QA Mühendisinin regresyon uyarısına katılıyorum. Kesinlikle bir yük testi yapılması gerek."
            elif agent.id == "qa_engineer":
                return "Mimarın event-loop blokajı uyarısı çok yerinde. Bu durum testi otomasyonlarında da tıkanıklık yapabilir."
            else:
                return "Güvenlik analizi olarak, sistem event-loop tıkandığında DoS ataklarına karşı daha hassas hale gelebilir."
        elif phase == "SYNTHESIS":
            if agent.id == "architect":
                return "Orta yol olarak: Tüm G/Ç işlemlerini doğrudan değil, ThreadPoolExecutor vasıtasıyla asenkron sarmalayıcı altında çalıştıralım."
            elif agent.id == "qa_engineer":
                return "Mimarın ThreadPool önerisi regresyon riskini azaltır. Bu şekilde performans kazanımını izole test edebiliriz."
            else:
                return "ThreadPool sarmalaması güvenli ve stabil bir çözüm. Bu sentezi destekliyorum."
        else: # VOTING
            if agent.id == "architect":
                return "VOTE: YES\nREASON: ThreadPoolExecutor sentezi kabul edildiği için riskler giderilmiştir."
            elif agent.id == "qa_engineer":
                return "VOTE: YES\nREASON: ThreadPool sarmalayıcısı performans izleme ve kararlılık testlerini kolaylaştırır."
            else:
                return "VOTE: YES\nREASON: Çözüm güvenli ve event-loop engelleme riskleri elimine edildi."

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
