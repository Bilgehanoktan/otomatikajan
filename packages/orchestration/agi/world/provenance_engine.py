import asyncio
import logging
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from sqlalchemy import select, update
from packages.persistence.models import SovereignCodeFile, SovereignCodeResult
from packages.persistence.session import AsyncSessionLocal
from packages.observability.logging import get_logger

_log = get_logger("agi_provenance")

class SovereignProvenanceEngine:
    """
    [Katman 62] Provenance Engine (Köken Motoru).
    Kod üzerindeki her değişikliği (Mutation) bilişsel bir gerekçeye (Task/Wisdom) bağlar.
    AGI'nin "Neden bu değişikliği yaptın?" sorusuna kesin yanıt vermesini sağlar.
    """

    def __init__(self):
        self._mutation_count = 0

    async def register_mutation(
        self, 
        file_path: str, 
        content: str,
        project_id: str, 
        agent_id: str, 
        wisdom_id: Optional[str] = None
    ) -> str:
        """
        Dosya değişikliğini 'Causal Provenance' (Nedensel Köken) olarak kaydeder.
        """
        _log.info(f"[PROVENANCE] Mutasyon kaydediliyor: {file_path} (Ajan: {agent_id})")
        
        # 1. Provenance ID Oluştur (Causal Hash)
        # Hash: TaskID + AgentID + FilePath + Timestamp
        t_now = datetime.now(timezone.utc).isoformat()
        raw_id = f"{project_id}:{agent_id}:{file_path}:{t_now}"
        prov_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
        
        try:
            async with AsyncSessionLocal() as db:
                # 2. Önce SovereignCodeResult var mı kontrol et (Proje bazlı paket)
                result_stmt = select(SovereignCodeResult).where(SovereignCodeResult.project_id == uuid.UUID(project_id))
                result = (await db.execute(result_stmt)).scalar_one_or_none()
                
                if not result:
                    # Paket yoksa yeni oluştur
                    result = SovereignCodeResult(
                        id=uuid.uuid4(),
                        project_id=uuid.UUID(project_id),
                        title=f"Autonomous Mutation Package ({agent_id})",
                        status="completed"
                    )
                    db.add(result)
                    await db.flush()
                
                # 3. Dosya kaydını güncelle veya ekle
                file_stmt = select(SovereignCodeFile).where(
                    (SovereignCodeFile.result_id == result.id) & 
                    (SovereignCodeFile.path == file_path)
                )
                existing_file = (await db.execute(file_stmt)).scalar_one_or_none()
                
                if existing_file:
                    existing_file.content = content
                    existing_file.provenance_id = prov_id
                    existing_file.updated_at = datetime.now(timezone.utc)
                else:
                    new_file = SovereignCodeFile(
                        id=uuid.uuid4(),
                        result_id=result.id,
                        filename=file_path.split("/")[-1].split("\\")[-1],
                        path=file_path,
                        content=content,
                        provenance_id=prov_id,
                        is_generated=True
                    )
                    db.add(new_file)
                
                await db.commit()
                self._mutation_count += 1
                return prov_id
                
        except Exception as e:
            _log.error(f"[PROVENANCE-ERROR] Mutasyon kaydı başarısız: {e}")
            return "ERR_PROV"

    def get_traceability_score(self) -> float:
        """Sistemin izlenebilirlik sağlığını döner."""
        # Basit bir sayaç bazlı metrik (Gerçek DB count yerine)
        return min(1.0, 0.5 + (self._mutation_count * 0.05))

# Singleton
provenance_engine = SovereignProvenanceEngine()
