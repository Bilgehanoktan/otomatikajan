"""
Synaptic Cortex (Phase 22) — Universal Cognitive Memory Layer.
(Unified from CognitiveSynapse and SynapticMemory)
Bellek & RAG Sistemi: Bilişsel Sinapslar aracılığıyla deneyimleri konsolide eder ve semantik geri çağırma sağlar.
"""
from __future__ import annotations
import hashlib
import os
import uuid
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import select, desc, func
from db.models import Memory
from observability.logging import get_logger
from core.agi.consciousness.affective_core import affective_core

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_log = get_logger("agi_synaptic_cortex")

def _np():
    import numpy as np
    return np

async def get_embedding(text_: str) -> list[float] | None:
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        return None
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                'https://api.openai.com/v1/embeddings',
                headers={'Authorization': f'Bearer {api_key}'},
                json={'model': 'text-embedding-3-small', 'input': text_},
            )
            resp.raise_for_status()
            return resp.json()['data'][0]['embedding']
    except Exception as e:
        _log.warning(f"Embedding API hatası: {e}")
        return None

from collections import deque
from observability.memory_governor import memory_governor

class UnifiedGalacticCortex:
    """
    Korteks Katmanı (Katman 30): Unified Galactic Cortex (UGC).
    AGI'nin evrensel bilişsel bellek merkezi. 
    Hem kalıcı (PostgreSQL) hem de hızlı (In-memory) erişim sağlar.
    """
    
    def __init__(self, cache_size: int = 100):
        self.knowledge_dir = "knowledge"
        os.makedirs(self.knowledge_dir, exist_ok=True)
        
        # Faz 30: In-memory Hot Cache (RSS koruması için sınırlı)
        self._hot_cache: deque[Dict[str, Any]] = deque(maxlen=cache_size)
        
        # Memory Governor'a kaydol (Hafıza dolduğunda cache'i temizle)
        memory_governor.register_cleanup_callback(self.prune_hot_cache)
        _log.info(f"[UGC] Başlatıldı. Hot Cache boyutu: {cache_size}")

    def prune_hot_cache(self):
        """MemoryGovernor tarafından tetiklenen acil durum temizliği."""
        count = len(self._hot_cache)
        self._hot_cache.clear()
        _log.warning(f"[UGC-PRUNE] Hot Cache temizlendi. {count} kayıt silindi.")

    async def save(
        self,
        db: AsyncSession,
        agent_id: str,
        body: str,
        category: str = "general",
        project_id: Optional[str] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> Memory:
        """Deneyimi kaydeder ve Hot Cache'e ekler."""
        final_metadata = metadata or {}
        if "signature" not in final_metadata:
            final_metadata["signature"] = uuid.uuid4().hex # Basitleştirilmiş imza
            
        # Faz 12.4: Duygusal Bağlam (Affective Context) Mührü
        if "affective_context" not in final_metadata:
            final_metadata["affective_context"] = affective_core.get_state_matrix()

        entry = Memory(
            id=uuid.uuid4(),
            agent_id=agent_id,
            body=body,
            category=category,
            project_id=str(project_id) if project_id else None,
            importance=importance,
            metadata_=final_metadata,
            tags=tags or [],
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )
        
        # DB'ye ekle (Eğer session varsa)
        if db is not None:
            db.add(entry)
            await db.flush()
        else:
            _log.debug("[UGC-SAVER] No DB session. Saving to Hot Cache only.")

        # Hot Cache'e ekle (UI ve hızlı geri çağırma için)
        cache_item = {
            "id": str(entry.id),
            "body": body,
            "category": category,
            "agent_id": agent_id,
            "importance": importance,
            "created_at": entry.created_at.isoformat()
        }
        self._hot_cache.append(cache_item)
        
        _log.info(f"[UGC-SAVER] Saved: [{category}] from {agent_id}. Importance: {importance}")
        return entry

    async def get_hot_memories(self) -> List[Dict[str, Any]]:
        """Hızlı erişim için in-memory cache'deki kayıtları döner."""
        return list(self._hot_cache)

    async def save_episode(self, db: AsyncSession, episode_data: dict) -> Memory:
        """Bir görevin tam yaşam döngüsünü (Episode) kaydeder."""
        project_id = episode_data.get("project_id")
        title = episode_data.get("title", "Unknown Task")
        status = episode_data.get("status", "unknown")
        
        body = f"Episode: {title}\nStatus: {status}\nSummary: {episode_data.get('summary', '')}"
        return await self.save(
            db=db,
            agent_id="system",
            body=body,
            category="episode_record",
            project_id=project_id,
            importance=0.7,
            metadata=episode_data,
            tags=["episode", status]
        )

    async def save_negative_lesson(self, db: AsyncSession, agent_id: str, body: str, importance: float = 0.7, metadata: dict = None) -> Memory:
        """Hata durumlarını ve 'yapılmaması gerekenleri' hafızaya işler."""
        return await self.save(
            db=db,
            agent_id=agent_id,
            body=f"[FAILURE] {body}",
            category="negative_lesson",
            importance=importance,
            metadata=metadata or {},
            tags=["failure", "lesson"]
        )

    async def save_architectural_inhibition(self, db: AsyncSession, rule_id: str, target: str, description: str) -> Memory:
        """Faz 42: Yasaklı mimari pratikleri ve dizinleri hafızaya 'inhibition' (ketleme) olarak işler."""
        return await self.save(
            db=db,
            agent_id="governance_watchdog",
            body=f"[INHIBITION] {rule_id}: {description} (Target: {target})",
            category="arch_inhibition",
            importance=0.9,
            metadata={"rule_id": rule_id, "target": target},
            tags=["governance", "inhibition", "architectural"]
        )

    async def save_skill(self, db: AsyncSession, skill_data: dict) -> Memory:
        body = f"Skill Artifact: {skill_data.get('name')}\nPurpose: {skill_data.get('description')}"
        return await self.save(
            db=db,
            agent_id="system",
            body=body,
            category="skill_artifact",
            importance=0.8,
            metadata=skill_data,
            tags=["skill", "artifact"]
        )

    async def save_policy(self, db: AsyncSession, policy_data: dict) -> Memory:
        body = f"Policy Proposal: {policy_data.get('title')}\nLogic: {policy_data.get('proposed_rule')}"
        return await self.save(
            db=db,
            agent_id="strategy_tuner",
            body=body,
            category="policy_proposal",
            importance=0.9,
            metadata=policy_data,
            tags=["policy", "governance"]
        )

    async def save_thought_thread(self, db: AsyncSession, thought: str, context_id: str = "global") -> Memory:
        """Faz 45: Bilişsel Devamlılık için 'Düşünce Zinciri' (Thought Thread) kaydeder."""
        return await self.save(
            db=db,
            agent_id="central_executive",
            body=thought,
            category="thought_thread",
            importance=0.8,
            metadata={"context_id": context_id},
            tags=["continuity", "internal_monologue"]
        )

    async def get_continuous_monologue(self, db: AsyncSession, limit: int = 5) -> str:
        """Faz 45: Son düşünce zincirlerini birleştirerek bilişsel devamlılık sağlar."""
        memories = await self.search(
            db=db,
            query="",
            category="thought_thread",
            top_k=limit
        )
        if not memories: return "Bilişsel devamlılık başlatılıyor..."
        # En yeniden en eskiye doğru birleştir
        threads = [m['body'] for m in reversed(memories)]
        return "\n>>> ".join(threads)

    async def synthesize_global_knowledge(self, db: AsyncSession, top_k: int = 20) -> List[Memory]:
        """Global bir 'bilgelik' katmanında birleştirir."""
        stmt = select(Memory).where(
            (Memory.importance >= 0.8) & 
            (Memory.category.in_(["policy_proposal", "episode_record", "reflection_log"]))
        ).order_by(desc(Memory.created_at))
        
        result = await db.execute(stmt.limit(top_k))
        top_memories = result.scalars().all()
        
        for m in top_memories:
            if "universal" not in (m.tags or []):
                m.tags = (m.tags or []) + ["universal"]
        
        return list(top_memories)

    async def get_negative_patterns(self, db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
        """Sistemdeki tekrarlayan hata ve negatif ders örüntülerini getirir."""
        return await self.search(
            db=db,
            query="",
            category="negative_lesson",
            top_k=limit
        )

    async def get_architectural_inhibitions(self, db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
        """Faz 42: Kayıtlı mimari kısıtlamaları getirir."""
        return await self.search(
            db=db,
            query="",
            category="arch_inhibition",
            top_k=limit
        )

    async def search(
        self,
        db: AsyncSession,
        query: str,
        agent_id: Optional[str] = None,
        category: Optional[str] = None,
        project_id: Optional[str] = None,
        top_k: int = 10,
        token_budget: int = 2500
    ) -> List[Dict[str, Any]]:
        """UGC Hibrit Arama (Hot Cache + DB Fallback)."""
        
        # 1. Önce Hot Cache'de ara
        results = []
        if query:
            q_lower = query.lower()
            for m in self._hot_cache:
                if q_lower in m["body"].lower():
                    results.append(m)
                    if len(results) >= top_k: return results

        db_results = []
        if db is not None:
            stmt = select(Memory).order_by(desc(Memory.importance), desc(Memory.created_at))
            if agent_id: stmt = stmt.where(Memory.agent_id == agent_id)
            if category: stmt = stmt.where(Memory.category == category)
            if project_id: stmt = stmt.where(Memory.project_id == str(project_id))
            stmt = stmt.where((Memory.expires_at == None) | (Memory.expires_at > datetime.now(timezone.utc)))
                
            if query:
                stmt = stmt.where(Memory.body.ilike(f"%{query}%"))
                
            result = await db.execute(stmt.limit(top_k))
            rows = result.scalars().all()
            
            db_results = [
                {
                    "id": str(m.id),
                    "agent_id": m.agent_id,
                    "body": m.body,
                    "category": m.category,
                    "importance": m.importance,
                    "metadata": m.metadata_,
                    "created_at": m.created_at.isoformat()
                } for m in rows
            ]
        
        # Birleştir (Tekil ID'lerle)
        seen_ids = {r["id"] for r in results}
        for r in db_results:
            if r["id"] not in seen_ids:
                results.append(r)
        
        return results[:top_k]

# Registry / Singleton Instance
ugc = UnifiedGalacticCortex()
synaptic_cortex = ugc # Backward compatibility

# Compatibility Aliases
memory_store = ugc
synaptic_memory = ugc
galaxy_cortex = ugc
