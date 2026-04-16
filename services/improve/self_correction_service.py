import asyncio
import uuid
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from pathlib import Path

from services.observability.logging import get_logger
from libs.llm.model_orchestrator import ModelOrchestrator
from services.orchestration.application.self_updater import SelfUpdater
from services.improve.diagnosis_engine import DiagnosisEngine
from services.improve.rollout_manager import RolloutManager
from services.improve.risk_scoring import RiskScoring
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import OperationalIncident, SystemImprovement, Project, SovereignEvidence
from services.orchestration.calibration_engine import calibration_engine
from sqlalchemy import select

logger = get_logger("self_correction_service")

class SelfCorrectionService:
    """
    Ana orkestratör: Olaylar -> Teşhis -> Risk Analizi -> Canary Rollout (Faz 16).
    """

    def __init__(self, model_orch: ModelOrchestrator, project_root: str):
        self.model_orch = model_orch
        self.project_root = project_root
        self.diagnosis_engine = DiagnosisEngine(model_orch, project_root)
        self.risk_scoring = RiskScoring()

    async def log_evidence(self, session, evidence_type: str, severity: str, 
                         project_id: Optional[UUID] = None, 
                         incident_id: Optional[UUID] = None,
                         improvement_id: Optional[UUID] = None,
                         payload: Dict[str, Any] = None):
        """Phase 26: R-01 Live Field Evidence Logger"""
        try:
            evidence = SovereignEvidence(
                evidence_type=evidence_type,
                severity=severity,
                project_id=project_id,
                incident_id=incident_id,
                improvement_id=improvement_id,
                payload=payload or {},
                created_at=datetime.now(timezone.utc)
            )
            session.add(evidence)
            # Biz bÃ¼yÃ¼k ihtimalle dÄ±ÅŸarÄ±daki session.commit()'i bekliyoruz ama 
            # kritik kanÄ±t iÃ§in flush yapabiliriz.
            await session.flush()
            logger.debug(f"📊 Evidence Logged: {evidence_type} (Incident: {incident_id})")
        except Exception as e:
            logger.error(f"Failed to log evidence: {e}")

    async def process_incident(self, incident_id: UUID) -> str:
        """
        Belirli bir olayı teşhis eder ve Faz 16 politikasına göre (Canary) düzeltir.
        """
        async with AsyncSessionLocal() as session:
            # 0. Load Incident
            incident = await session.get(OperationalIncident, incident_id)
            if not incident:
                return f"Hata: Olay {incident_id} bulunamadı."

            if incident.status == "resolved":
                return f"Olay {incident_id} zaten çözülmüş."

            # Load Project context
            is_pilot = False
            if incident.project_id:
                project = await session.get(Project, incident.project_id)
                if project and project.is_pilot:
                    is_pilot = True

            logger.info(f"🔍 Processing incident {incident.id}... Pilot={is_pilot} Type={incident.incident_type}")

            # 1. Diagnosis
            target_file, instruction = await self.diagnosis_engine.diagnose(
                incident_id=str(incident.id),
                incident_type=incident.incident_type,
                message=incident.message,
                payload=incident.payload or {}
            )

            if not target_file:
                logger.warning(f"Diagnosis failed for incident {incident.id}: No target file found.")
                await self.log_evidence(
                    session, "self_healing_failed", "error", 
                    incident.project_id, incident.id, 
                    payload={"reason": "diagnosis_failed", "details": "No target file identified"}
                )
                return "Teşhis başarısız: Hedef dosya belirlenemedi."

            # 2. Risk Assessment (Dosya yolu ve talimat bazlı ön değerlendirme)
            risk_eval = self.risk_scoring.evaluate_path_and_instruction(target_file, instruction)
            risk_score = risk_eval["score"]

            # Log Diagnosis & Risk Evidence
            await self.log_evidence(
                session, "self_healing_assessment", "info",
                incident.project_id, incident.id,
                payload={
                    "target_file": target_file,
                    "instruction": instruction,
                    "risk_score": risk_score,
                    "risk_factors": risk_eval.get("factors", []),
                    "diagnosis_logic": "phase_17_incident_to_file_mapping"
                }
            )
            
            # 3. Create SystemImprovement Record
            # Daha önce bu dosya için bekleyen bir işlem olup olmadığını kontrol et
            stmt = select(SystemImprovement).where(
                SystemImprovement.target_file == target_file,
                SystemImprovement.status.in_(["pending", "canary"])
            )
            existing_res = await session.execute(stmt)
            if existing_res.scalars().first():
                return f"Zaten {target_file} için aktif bir iyileştirme süreci var. Çakışma önlendi."

            improvement = SystemImprovement(
                id=uuid.uuid4(),
                target_file=target_file,
                instruction=instruction,
                risk_score=risk_score,
                status="pending",
                created_at=datetime.now(timezone.utc)
            )
            session.add(improvement)
            await session.commit()
            await session.refresh(improvement)

            # R-05 Calibration Loop: Record the proposal
            calibration_engine.record_correction(
                incident_id=str(incident.id),
                action="proposal",
                risk_score=risk_score,
                severity=incident.severity if hasattr(incident, 'severity') else "medium"
            )

            # 4. Phase 16 Policy: L3 Autonomy for Pilot Projects + Low-Risk Changes
            # Otonomi eşiği: risk_score < 0.25
            if is_pilot and risk_score < 0.25:
                logger.warning(f"🚀 AUTO-CANARY STARTING: Incident {incident.id} -> File {target_file} (Risk: {risk_score})")
                
                # RolloutManager üzerinden Canary başlat
                rollout_mgr = RolloutManager(session, self.project_root, self.model_orch)
                
                await self.log_evidence(
                    session, "self_healing_rollout", "warning",
                    incident.project_id, incident.id, improvement.id,
                    payload={"action": "auto_canary_init", "duration": "15m", "isolation": "pilot"}
                )

                success = await rollout_mgr.apply_canary(improvement.id)
                
                if success:
                    # Incident'ı 'investigating' durumuna çek (Canary bitene kadar bekle)
                    incident.status = "investigating"
                    await session.commit()
                    return f"Başarılı. Otonom Canary başlatıldı (15 dk). İyileştirme ID: {improvement.id}"
                else:
                    incident.status = "failed"
                    await self.log_evidence(
                        session, "self_healing_failed", "critical",
                        incident.project_id, incident.id, improvement.id,
                        payload={"action": "auto_canary_failed", "reason": "rollout_manager_error"}
                    )
                    await session.commit()
                    return f"Hata: Otonom düzeltme uygulanırken bir sorun oluştu."
            else:
                logger.info(f"⏸ Manual Approval Required: Risk={risk_score}, Pilot={is_pilot}")
                # R-05 Calibration Loop: Record the gate block
                calibration_engine.record_correction(
                    incident_id=str(incident.id),
                    action="blocked_by_gate",
                    risk_score=risk_score,
                    severity=incident.severity if hasattr(incident, 'severity') else "medium"
                )
                return f"Önerilen İyileştirme ({improvement.id}) oluşturuldu. Risk nedeniyle manuel onay bekleniyor."
id}) oluşturuldu. Manuel onay bekleniyor."
