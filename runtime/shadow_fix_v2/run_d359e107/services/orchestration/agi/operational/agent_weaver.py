import os
import json
from typing import Optional, Dict, List, Any
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

_log = get_logger("agi_agent_weaver")

class AgentWeaver:
    """
    Operation Core (Katman 11): Cognitive Capability Expansion.
    Yeni uzman ajanlar (Specialists) sentezleyerek sistemin bilişsel sınırlarını genişletir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.dynamic_path = os.path.join("agents", "dynamic_agents.json")

    async def synthesize_specialist(self, domain: str) -> bool:
        """
        Belirli bir uzmanlık alanı için yeni bir ajan sentezler.
        """
        _log.info(f"Yeni uzman ajan sentezleniyor: {domain}")
        
        prompt = f"""
        Sistem için yeni bir uzman ajan (Specialist Agent) tasarla.
        Uzmanlık Alanı: {domain}
        
        Lütfen ajanın özelliklerini JSON formatında belirt:
        {{
            "id": "ajan_id_snake_case",
            "name": "Ajanın İnsan Okunabilir İsmi",
            "emoji": "Bir emoji",
            "role": "Kısa rol tanımı",
            "system_prompt": "Ajanın uyması gereken detaylı talimatlar ve uzmanlık kuralları"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Mimarısın. Sistemin yeteneklerini genişletmek için yeni uzmanlık birimleri tasarlarsın."
            )
            
            agent_data = self._parse_json(response.content)
            if not agent_data:
                return False
                
            return self._register_agent(agent_data)
            
        except Exception as e:
            _log.error(f"Ajan sentezleme hatası: {e}")
            return False

    def _register_agent(self, data: Dict[str, Any]) -> bool:
        """Ajanı dynamic_agents.json dosyasına ekler."""
        try:
            agents = []
            if os.path.exists(self.dynamic_path):
                with open(self.dynamic_path, "r", encoding="utf-8") as f:
                    try:
                        agents = json.load(f)
                    except json.JSONDecodeError:
                        agents = []
            
            # Çakışma kontrolü
            if any(a.get("id") == data.get("id") for a in agents):
                _log.warning(f"Ajan {data.get('id')} zaten mevcut.")
                return True
                
            agents.append(data)
            
            os.makedirs(os.path.dirname(self.dynamic_path), exist_ok=True)
            with open(self.dynamic_path, "w", encoding="utf-8") as f:
                json.dump(agents, f, indent=4, ensure_ascii=False)
                
            _log.info(f"Dinamik ajan başarıyla kaydedildi: {data.get('id')}")
            return True
        except Exception as e:
            _log.error(f"Ajan kaydetme hatası: {e}")
            return False

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return None

# --- Singleton ---
agent_weaver = AgentWeaver()
