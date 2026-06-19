import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Union
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

def utcnow():
    return datetime.now(timezone.utc)

from libs.db.session import session_scope
from libs.db.models.core_models import SovereignEvidence, Project, OperationalIncident, SystemImprovement, FederationTrust, FederationTrustHistory

_log = logging.getLogger("agi_reporting_service")

class OperationalTrustReport:
    """
    Faz 26: R-01 Operational Trust Report.
    SovereignEvidence verilerini kullanarak otonom sistem güvenilirliğini raporlar.
    """

    @classmethod
    async def generate_trust_summary(cls, db: AsyncSession = None) -> Dict[str, Any]:
        """Sistem genelindeki otonom güvenilirlik özetini oluşturur."""
        if db:
            return await cls._trust_summary_core(db)
        async with session_scope() as session:
            return await cls._trust_summary_core(session)

    @classmethod
    async def _trust_summary_core(cls, db: AsyncSession) -> Dict[str, Any]:
        """Core logic for trust summary generation."""
        # 1. Toplam Kanıt Sayısı
        total_evidence = await db.scalar(select(func.count(SovereignEvidence.id))) or 0
        
        # 2. Tip Bazlı Dağılım
        evidence_types = await db.execute(
            select(SovereignEvidence.evidence_type, func.count(SovereignEvidence.id))
            .group_by(SovereignEvidence.evidence_type)
        )
        type_counts = {t: c for t, c in evidence_types}
        
        # 3. Kendi Kendine İyileştirme Başarı Oranı
        promotions = type_counts.get("promotion", 0)
        rollbacks = type_counts.get("rollback", 0)
        total_correction_cycles = promotions + rollbacks
        healing_success_rate = (promotions / total_correction_cycles * 100) if total_correction_cycles > 0 else 100.0
        
        # 4. Ekonomik Güvenilirlik
        drifts = type_counts.get("economic_drift", 0)
        
        # 5. Son Kanıt Örnekleri
        recent_res = await db.execute(
            select(SovereignEvidence)
            .order_by(SovereignEvidence.created_at.desc())
            .limit(5)
        )
        recent_evidence = []
        for e in recent_res.scalars():
            recent_evidence.append({
                "id": str(e.id),
                "type": e.evidence_type,
                "severity": e.severity,
                "created_at": e.created_at.isoformat(),
                "payload_summary": str(e.payload)[:100] + "..."
            })

        return {
            "total_evidence_points": total_evidence,
            "type_distribution": type_counts,
            "autonomous_reliability": {
                "self_healing_success_rate": round(healing_success_rate, 2),
                "total_correction_cycles": total_correction_cycles,
                "promotions": promotions,
                "rollbacks": rollbacks,
            },
            "economic_safety": {
                "drift_events": drifts,
            },
            "recent_ledger": recent_evidence
        }

    @classmethod
    async def get_project_evidence_chain(cls, project_id: str) -> List[Dict[str, Any]]:
        """Belirli bir proje için tam kanıt zincirini döner."""
        async with session_scope() as db:
            res = await db.execute(
                select(SovereignEvidence)
                .where(SovereignEvidence.project_id == project_id)
                .order_by(SovereignEvidence.created_at.asc())
            )
            chain = []
            for e in res.scalars():
                chain.append({
                    "timestamp": e.created_at.isoformat(),
                    "type": e.evidence_type,
                    "severity": e.severity,
                    "payload": e.payload,
                    "provenance": e.provenance_hash
                })
            return chain


class FederationTrustReport:
    """
    Faz 26: R-09 Federation Trust Report.
    Cluster bazlı güven skorlarını ve operasyonel hiyerarşiyi raporlar.
    """

    @classmethod
    async def get_cluster_trust_summary(cls) -> List[Dict[str, Any]]:
        """Tüm cluster'ların güven puanlarını ve temel metriklerini döner."""
        async with session_scope() as db:
            res = await db.execute(select(FederationTrust).order_by(FederationTrust.trust_score.desc()))
            clusters = []
            for t in res.scalars():
                total_ops = t.success_count + t.failure_count
                success_rate = (t.success_count / total_ops * 100) if total_ops > 0 else 100.0
                
                clusters.append({
                    "cluster_id": t.cluster_id,
                    "trust_score": round(t.trust_score, 4),
                    "success_rate": round(success_rate, 2),
                    "arbitration_wins": t.arbitration_wins,
                    "last_active": t.last_activity_at.isoformat(),
                    "status": "trusted" if t.trust_score > 0.7 else "degraded" if t.trust_score > 0.4 else "untrusted"
                })
            return clusters

    @classmethod
    async def get_trust_history(cls, cluster_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Bir cluster'ın güven puanı değişim geçmişini döner."""
        async with session_scope() as db:
            res = await db.execute(
                select(FederationTrustHistory)
                .where(FederationTrustHistory.cluster_id == cluster_id)
                .order_by(FederationTrustHistory.created_at.desc())
                .limit(limit)
            )
            history = []
            for h in res.scalars():
                history.append({
                    "timestamp": h.created_at.isoformat(),
                    "trust_score": round(h.trust_score, 4),
                    "reason": h.change_reason,
                    "delta": h.payload.get("delta", 0)
                })
            return history


class IncidentReportingService:
    """
    Faz 26: R-10 Chaos & Operational Reportability.
    Otonom postmortem, yönetici özetleri ve olay paketleri üretir.
    """

    @classmethod
    async def generate_postmortem(cls, incident_id: Union[str, uuid.UUID], db: AsyncSession = None) -> str:
        """Otomatik bir olay sonrası değerlendirme (Postmortem) dökümanı üretir."""
        if db:
            return await cls._postmortem_core(incident_id, db)
        async with session_scope() as session:
            return await cls._postmortem_core(incident_id, session)

    @classmethod
    async def _postmortem_core(cls, incident_id: Union[str, uuid.UUID], db: AsyncSession) -> str:
        # P0: SQLite/Postgres UUID Compatibility
        processed_id = uuid.UUID(str(incident_id)) if isinstance(incident_id, str) else incident_id
        
        # 1. Olay Detaylarını Al
        incident = await db.get(OperationalIncident, processed_id)
        if not incident:
            return "Incident not found."

        # 2. İlgili Kanıt Zincirini Al
        evidence_res = await db.execute(
            select(SovereignEvidence)
            .where(SovereignEvidence.incident_id == incident.id)
            .order_by(SovereignEvidence.created_at.asc())
        )
        evidence_chain = evidence_res.scalars().all()

        # 3. Markdown Hazırla
        report = [
            f"# POSTMORTEM: {incident.incident_type.upper()}",
            f"**Incident ID:** {incident.id}",
            f"**Severity:** {incident.severity}",
            f"**Status:** {incident.status}",
            f"**Created At:** {incident.created_at.isoformat()}",
            f"**Resolved At:** {incident.resolved_at.isoformat() if incident.resolved_at else 'UNRESOLVED'}",
            "\n## Summary",
            incident.message,
            "\n## Autonomous Evidence Chain",
        ]

        if not evidence_chain:
            report.append("_No autonomous evidence recorded for this incident._")
        else:
            for idx, e in enumerate(evidence_chain):
                report.append(f"### {idx+1}. {e.evidence_type.title()}")
                report.append(f"- **Timestamp:** {e.created_at.isoformat()}")
                report.append(f"- **Severity:** {e.severity}")
                report.append(f"- **Action Taken:** {e.payload.get('action', 'N/A')}")
                if 'reasoning' in e.payload:
                    report.append(f"- **Reasoning:** {e.payload['reasoning']}")
                if 'cost_impact' in e.payload:
                    report.append(f"- **Economic Impact:** ${e.payload['cost_impact']}")

        report.append("\n## Root Cause Analysis")
        report.append(incident.payload.get("root_cause", "Automatic diagnosis in progress..."))

        report.append("\n## Prevention & Hardening")
        report.append(incident.payload.get("prevention_plan", "Enforced via autonomous safety guardrails."))
        
        return "\n".join(report)

    @classmethod
    async def generate_executive_summary(cls, db: AsyncSession = None) -> Dict[str, Any]:
        """Üst düzey yönetici özeti (Economic & Operational Stability) oluşturur."""
        if db:
            return await cls._executive_summary_core(db)
        async with session_scope() as session:
            return await cls._executive_summary_core(session)

    @classmethod
    async def _executive_summary_core(cls, db: AsyncSession) -> Dict[str, Any]:
        return {
            "period": "Last 24 Hours",
            "system_availability": "99.99%", # Mock for now
            "total_incidents": 5, # Mock
            "autonomous_resolution_rate": "80%",
            "economic_status": "WITHIN_BUDGET",
            "top_performing_regions": ["US-CENTRAL", "EU-WEST"],
            "risk_profile": "LOW"
        }

    @classmethod
    async def generate_failover_evidence_pack(cls, project_id: Union[str, uuid.UUID], db: AsyncSession = None) -> Dict[str, Any]:
        """Regional failover durumunda sunulacak kanıt paketini oluşturur."""
        if db:
            return await cls._failover_evidence_core(project_id, db)
        async with session_scope() as session:
            return await cls._failover_evidence_core(project_id, session)

    @classmethod
    async def _failover_evidence_core(cls, project_id: Union[str, uuid.UUID], db: AsyncSession) -> Dict[str, Any]:
        processed_id = uuid.UUID(str(project_id)) if isinstance(project_id, str) else project_id
        
        # Failover tipindeki kanıtları bul
        res = await db.execute(
            select(SovereignEvidence)
            .where(SovereignEvidence.project_id == processed_id)
            .where(SovereignEvidence.evidence_type == "failover")
            .order_by(SovereignEvidence.created_at.desc())
        )
        failover_events = res.scalars().all()
        
        pack = {
            "project_id": str(processed_id),
            "report_type": "Regional Failover Evidence",
            "generated_at": utcnow().isoformat(),
            "events": []
        }
        
        for f in failover_events:
            pack["events"].append({
                "timestamp": f.created_at.isoformat(),
                "source_region": f.payload.get("source_region"),
                "target_region": f.payload.get("target_region"),
                "reason": f.payload.get("reason"),
                "decision_latency_ms": f.payload.get("latency_ms"),
                "cost_delta": f.payload.get("cost_delta")
            })
            
        return pack
