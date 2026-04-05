"""
Cognitive Synapse (Phase 20) — Restore and Evolve.
Hafıza bütünlüğünü korur ve AGI seviyesinde semantik arama sağlar.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Memory
from observability.logging import get_logger

_log = get_logger("cognitive_synapse")

class CognitiveSynapse:
    """
    Katman 7 (Memory & Learning): Uzun vadeli bellek ve RAG arayüzü.
    Eski adıyla MemoryStore. Proje bazlı izolasyon ve önem derecesine göre arama yapar.
    """

    async def save(
        self,
        db: AsyncSession,
        agent_id: str,
        body: str,
        category: str = "general",
        project_id: Optional[str] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Memory:
        """Deneyimi PostgreSQL 'memories' tablosuna kaydeder (Hafıza Silme Yok kuralı)."""
        entry = Memory(
            id=uuid.uuid4(),
            agent_id=agent_id,
            body=body,
            category=category,
            project_id=str(project_id) if project_id else None,
            importance=importance,
            metadata_=metadata or {},
            tags=tags or [],
            created_at=datetime.now(timezone.utc)
        )
        db.add(entry)
        await db.flush()
        _log.info(f"Synapse saved: [{category}] from {agent_id}. Importance: {importance}")
        return entry

    async def search(
        self,
        db: AsyncSession,
        query: str,
        agent_id: Optional[str] = None,
        category: Optional[str] = None,
        project_id: Optional[str] = None,
        top_k: int = 5,
        token_budget: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        Semantik veya keyword bazlı arama (Şu an SQL fallback).
        Gelecekte pgvector 'Vector' tipi ile güncellenecek.
        """
        stmt = select(Memory).order_by(desc(Memory.importance), desc(Memory.created_at))
        
        if agent_id:
            stmt = stmt.where(Memory.agent_id == agent_id)
        if category:
            stmt = stmt.where(Memory.category == category)
        if project_id:
            stmt = stmt.where(Memory.project_id == str(project_id))
            
        # Basit keyword fallback arama
        if query:
            stmt = stmt.where(Memory.body.ilike(f"%{query}%"))
            
        result = await db.execute(stmt.limit(top_k))
        memories = []
        for m in result.scalars().all():
            memories.append({
                "id": str(m.id),
                "agent_id": m.agent_id,
                "body": m.body,
                "category": m.category,
                "importance": m.importance,
                "metadata": m.metadata_,
                "created_at": m.created_at.isoformat()
            })
        return memories

    async def get_recent(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        limit: int = 15
    ) -> List[Memory]:
        """En son deneyimleri getirir (Örn: Policy synthesis için)."""
        stmt = select(Memory).order_by(desc(Memory.created_at))
        if category:
            stmt = stmt.where(Memory.category == category)
        
        result = await db.execute(stmt.limit(limit))
        return list(result.scalars().all())

    async def save_policy(self, db: AsyncSession, data: Dict[str, Any]) -> Memory:
        """Yeni sentezlenen politikayı kalıcı hale getirir."""
        return await self.save(
            db=db,
            agent_id="strategy_tuner",
            body=data.get("proposed_rule", ""),
            category="policy_proposal",
            importance=0.9,
            metadata=data
        )

    async def consolidate_experiences(self, db: AsyncSession, category: str, model_orch: Any) -> Optional[str]:
        """
        [Phase 22] Semantic Consolidation - Parçalı deneyimleri 'ders' olarak birleştirir.
        Biyolojik rüya görme/uyku evresine benzer şekilde, verileri soyutlaştırır.
        """
        recent = await self.get_recent(db, category=category, limit=20)
        if len(recent) < 5:
            return None # Yeterli veri yok
            
        _log.info(f"Semantik Konsolidasyon Başlatılıyor: [{category}] ({len(recent)} deneyim)")
        
        bodies = [m.body for m in recent if m.importance > 0.6]
        if not bodies: return None
        
        prompt = f"""
        Aşağıdaki {category} kategorisindeki deneyimleri analiz et ve aralarındaki ortak örüntüleri (patterns) bul.
        Bu deneyimlerden çıkarılabilecek en önemli 3 "Ders"i (Lessons Learned) özetle.
        
        DENEYİMLER:
        {chr(10).join(bodies)}
        
        Lütfen sentezlenen konsolide raporu Türkçe ver.
        """
        
        try:
            resp = await model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Hafıza Konsolidasyon (Semantic Consolidation) birimisin."
            )
            
            # Konsolide dersi yeni bir yüksek-önemli hafıza olarak kaydet
            await self.save(
                db=db,
                agent_id="memory_consolidator",
                body=resp.content,
                category=f"consolidated_{category}",
                importance=0.95,
                metadata={"source_memories": [str(m.id) for m in recent]}
            )
            return resp.content
        except Exception as e:
            _log.error(f"Consolidation hatası: {e}")
            return None

# Singleton Instance (compatibility name)
memory_store = CognitiveSynapse()
