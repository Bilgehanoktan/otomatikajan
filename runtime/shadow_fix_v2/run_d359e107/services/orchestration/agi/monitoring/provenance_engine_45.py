"""
Provenance Engine (Phase 41.2) — Evolutionary Traceability.
AGI'nin kendi üzerinde yaptığı her değişikliğin (Self-Modification) 
kök nedenini, politikasını ve kod farkını (diff) izleyen ve kaydeden birim.
"""
import difflib
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models import Memory
from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from services.observability.logging import get_logger

_log = get_logger("agi_provenance_engine")

class ProvenanceEngine45:
    """
    Bilişsel Köken Katman (Katman 45 - Sovereign): İzlenebilirlik.
    'Neden bu kod değişti?' sorusuna deterministik yanıt verir.
    """
    
    async def record_evolution_step(
        self, 
        db: AsyncSession, 
        file_path: str, 
        original_content: str, 
        new_content: str, 
        policy_id: str,
        reason: str
    ):
        """
        Bir evrim adımını dökümante eder.
        """
        try:
            # 1. Diff Üret
            diff = list(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"{file_path} (PRE-v45)",
                tofile=f"{file_path} (POST-v45)"
            ))
            diff_text = "".join(diff)

            # 2. Provenance Kaydı Oluştur
            provenance_payload = {
                "file_path": file_path,
                "policy_reference": policy_id,
                "reasoning": reason,
                "diff_summary": diff_text[:2000],  # İlk 2000 karakter (limitler dahilinde)
                "version": "45.0",
                "sovereign_id": "SOV-EVO-PROV-" + str(int(datetime.now(timezone.utc).timestamp()))
            }

            # 3. Synaptic Cortex üzerinden kalıcı hafızaya işle
            await synaptic_cortex.save(
                db=db,
                agent_id="provenance_engine_45",
                body=f"Sovereign Evolution: {file_path} refactored based on Policy {policy_id}.",
                category="evolution_provenance",
                importance=1.0, # En yüksek önem
                metadata=provenance_payload,
                tags=["provenance", "evolution", "v45", "traceability"]
            )
            
            _log.info(f"[PROVENANCE] Evrimsel iz kaydedildi: {file_path} (Policy: {policy_id})")

        except Exception as e:
            _log.error(f"[PROVENANCE] Kayıt hatası: {e}")

    async def get_lineage(self, db: AsyncSession, file_path: str) -> List[Memory]:
        """
        Bir dosyanın evrimsel soy ağacını (lineage) getirir.
        """
        stmt = select(Memory).where(
            Memory.category == "evolution_provenance",
            Memory.metadata_["file_path"].as_string() == file_path
        ).order_by(Memory.created_at.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()

from datetime import datetime, timezone
from sqlalchemy import select

# Singleton instance
provenance_engine_45 = ProvenanceEngine45()
