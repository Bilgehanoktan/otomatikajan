"""
Red-Team Agent — Phase 40
Sovereign AGI Karşıt Denetim (Adversarial Audit).
"""

import logging
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from llm.model_orchestrator import ModelOrchestrator

_log = logging.getLogger("agi_red_team")

@dataclass
class Vulnerability:
    issue: str
    severity: str # high, medium, low
    impact: str
    mitigation: str

@dataclass
class VulnerabilityReport:
    agent_id: str = "red_team"
    threat_score: float = 0.0 # 0 to 1 (1 = Plan is broken)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    confidence: float = 0.9

class RedTeamAgent:
    """
    Şeytanın Avukatı (Devil's Advocate).
    Planlardaki açıkları, halüsinasyonları ve güvenlik zayıflıklarını bulur.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def attack_plan(self, context: str, plan_body: str) -> VulnerabilityReport:
        """Önerilen planı acımasızca eleştirir ve zayıflıkları raporlar."""
        _log.info("[RED-TEAM] Dialektik Saldırı Başlatıldı.")

        prompt = f"""
        Aşağıdaki planı acımasız bir Red-Team Güvenlik Mimarı olarak incele. 
        Görevin bu plandaki açıkları, halüsinasyonları, tutarsızlıkları ve riskleri bulmak.

        BAĞLAM: {context[:500]}
        ÖNERİLEN PLAN:
        {plan_body}

        Lütfen plandaki en kritik 2-3 zayıf noktayı bul ve bir 'Tehdit Skoru' (0.0 - 1.0) belirle.
        (1.0 = Bu plan felaketle sonuçlanır, 0.0 = Plan çok sağlam)

        Yalnızca şu JSON formatında yanıtla:
        {{
            "threat_score": 0.XX,
            "findings": [
                {{
                    "issue": "Sorun nedir?",
                    "severity": "high/medium/low",
                    "impact": "Ne bozulur?",
                    "mitigation": "Nasıl önlenir?"
                }}
            ]
        }}
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect", # Red team architect
                prompt=prompt,
                system_prompt="Sen acımasız, şüpheci ve titiz bir Red-Team Mimarı'sın. Plana asla güvenme."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                
                vulns = [
                    Vulnerability(**f) for f in data.get("findings", [])
                ]
                
                return VulnerabilityReport(
                    threat_score=data.get("threat_score", 0.0),
                    vulnerabilities=vulns
                )
            
        except Exception as e:
            _log.error(f"[RED-TEAM] Saldırı başarısız: {e}")
        
        return VulnerabilityReport(threat_score=0.1) # Fallback low threat

# Singleton
red_team = RedTeamAgent()
