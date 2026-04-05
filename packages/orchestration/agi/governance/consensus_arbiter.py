import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from packages.orchestration.agi.task_governance import GovernedTask, GovernanceStatus
from core.agi.cognitive.consensus_manager import consensus_manager
from packages.orchestration.agi.schemas import PlanProposal
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_consensus_arbiter")

class ConsensusArbiter:
    """
    [Katman 61] Consensus Arbiter (Münazara Hakemi).
    Yüksek riskli veya düşük 'Reality Score' olan görevlerde çoklu ajan denetimini zorunlu kılar.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self._last_report: Dict[str, Any] = {}

    @property
    def _last_consensus_score(self) -> float:
        """Returns the consensus score from the last debate."""
        return self._last_report.get("consensus_score", 1.0)

    async def execute_debate(self, task: GovernedTask, context: str) -> tuple[bool, Dict[str, Any]]:
        """
        Görev üzerinde çoklu ajan münazarası (debate) başlatır ve ortak akıl kararı döner.
        """
        _log.info(f"[CONSENSUS-DEBATE] Başlatılıyor: {task.id} (Risk: {task.risk_level})")
        
        # 1. Proposal Hazırla (Mevcut plan + Alternatif Güvenlik Planı)
        # Faz 61: Dinamik olarak Security 'denetçi' teklifi üret
        security_critique_prompt = f"GÖREV: {task.prompt}\nBu görevi güvenlik ve veri bütünlüğü açısından eleştir ve alternatif bir güvenli yol öner."
        
        try:
            # Paralel olarak görüşleri topla
            responses = await asyncio.gather(
                self.model_orch.complete_task(
                    agent_role="architect",
                    prompt=f"Bu görev için en sağlam uygulama planını tekrar gözden geçir: {task.prompt}",
                    task_id=task.id
                ),
                self.model_orch.complete_task(
                    agent_role="security",
                    prompt=security_critique_prompt,
                    task_id=task.id
                )
            )
            
            proposals = [
                PlanProposal(agent_id="architect", content=responses[0].content if responses[0] else "", confidence=0.85),
                PlanProposal(agent_id="security", content=responses[1].content if responses[1] else "", confidence=0.90)
            ]
            
            # 2. ConsensusManager ile Çözümle
            report = await consensus_manager.resolve(
                topic=task.prompt,
                context=context,
                proposals=proposals
            )
            
            self._last_report = report
            score = report.get("consensus_score", 0.0)
            
            # --- Phase 61: Hard Veto Detect (Otonom Güvenlik) ---
            # Eğer Security ajanı veya Red-Team 'VETO' demişse veya skor çok düşükse reddet.
            veto_keywords = ["VETO", "BLOCK", "DENIED", "GÜVENLİK TEHDİDİ", "KRİTİK RİSK"]
            issued_veto = any(
                any(kw in p.content.upper() for kw in veto_keywords)
                for p in proposals if p.agent_id in ["security", "red_team"]
            )
            
            # 3. Karar ve Onay Eşiği
            if issued_veto:
                _log.error(f"[CONSENSUS-VETO] GÜVENLİK VETOSU TETİKLENDİ! Görev durduruluyor: {task.id}")
                return False, {**report, "error": "GÜVENLİK VETOSU: Ajanlar tarafından kritik risk tespit edildi."}

            if score >= 0.7:
                _log.info(f"[CONSENSUS-OK] Konsensüs sağlandı. Skor: {score}")
                return True, report
            else:
                _log.warning(f"[CONSENSUS-REJECT] Güven düzeyi yetersiz! Skor: {score}")
                return False, report
                
        except Exception as e:
            _log.error(f"[CONSENSUS-ERROR] Münazara hatası: {e}")
            return False, {"error": str(e), "consensus_score": 0.0}

# Singleton
consensus_arbiter = ConsensusArbiter()
