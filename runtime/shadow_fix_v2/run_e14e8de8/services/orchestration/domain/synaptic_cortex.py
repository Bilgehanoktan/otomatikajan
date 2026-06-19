from __future__ import annotations
import hashlib
import os
import uuid
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from collections import deque

from sqlalchemy import select, desc, func
from libs.db.models import Memory
from services.observability.logging import get_logger
from services.orchestration.domain.affective_core import affective_core
from services.observability.memory_governor import memory_governor

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_log = get_logger("agi_synaptic_cortex")

def _np():
    import numpy as np
    return np

async def get_embedding(text_: str) -> list[float] | None:
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key: return None
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post('https://api.openai.com/v1/embeddings', headers={'Authorization': f'Bearer {api_key}'}, json={'model': 'text-embedding-3-small', 'input': text_})
            resp.raise_for_status()
            return resp.json()['data'][0]['embedding']
    except Exception as e:
        _log.warning(f"Embedding API hatası: {e}")
        return None

class UnifiedGalacticCortex:
    def __init__(self, cache_size: int = 100):
        self.knowledge_dir = "knowledge"
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self._hot_cache: deque[Dict[str, Any]] = deque(maxlen=cache_size)
        memory_governor.register_cleanup_callback(self.prune_hot_cache)
        _log.info(f"[UGC] Başlatıldı. Hot Cache boyutu: {cache_size}")

    def prune_hot_cache(self):
        count = len(self._hot_cache)
        if count > 0:
            try:
                orphan_file = os.path.join(self.knowledge_dir, "orphan_memories.json")
                mode = 'a' if os.path.exists(orphan_file) else 'w'
                with open(orphan_file, mode, encoding='utf-8') as f:
                    for item in self._hot_cache: f.write(json.dumps(item) + "\n")
            except Exception as e: _log.error(f"[UGC-PRUNE] Error: {e}")
        self._hot_cache.clear()

    async def save(self, db: AsyncSession, agent_id: str, body: str, category: str = "general", project_id: Optional[str] = None, importance: float = 0.5, metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None, expires_at: Optional[datetime] = None, parent_id: Optional[uuid.UUID] = None, cause_id: Optional[uuid.UUID] = None) -> Memory:
        final_metadata = metadata or {}
        if "signature" not in final_metadata: final_metadata["signature"] = uuid.uuid4().hex
        if "affective_context" not in final_metadata: final_metadata["affective_context"] = affective_core.get_state_matrix()
        entry = Memory(id=uuid.uuid4(), agent_id=agent_id, body=body, category=category, project_id=str(project_id) if project_id else None, importance=importance, metadata_=final_metadata, tags=tags or [], expires_at=expires_at, parent_id=parent_id, cause_id=cause_id, created_at=datetime.now(timezone.utc))
        if db is not None:
            db.add(entry)
            await db.flush()
        cache_item = {"id": str(entry.id), "body": body, "category": category, "agent_id": agent_id, "importance": importance, "created_at": entry.created_at.isoformat()}
        self._hot_cache.append(cache_item)
        return entry

    async def get_hot_memories(self) -> List[Dict[str, Any]]: return list(self._hot_cache)

    async def save_episode(self, db: AsyncSession, episode_data: dict, parent_id: Optional[uuid.UUID] = None) -> Memory:
        return await self.save(db=db, agent_id="system", body=f"Episode: {episode_data.get('title')}", category="episode_record", project_id=episode_data.get("project_id"), importance=0.7, metadata=episode_data, tags=["episode"], parent_id=parent_id)

    async def save_negative_lesson(self, db: AsyncSession, agent_id: str, body: str, importance: float = 0.7, metadata: dict = None, parent_id: Optional[uuid.UUID] = None, cause_id: Optional[uuid.UUID] = None) -> Memory:
        return await self.save(db=db, agent_id=agent_id, body=f"[FAILURE] {body}", category="negative_lesson", importance=importance, metadata=metadata or {}, tags=["failure", "lesson"], parent_id=parent_id, cause_id=cause_id)

    async def save_thought_thread(self, db: AsyncSession, thought: str, context_id: str = "global") -> Memory:
        return await self.save(db=db, agent_id="central_executive", body=thought, category="thought_thread", importance=0.8, metadata={"context_id": context_id}, tags=["continuity"])

    async def search(self, db: AsyncSession, query: str, agent_id: Optional[str] = None, category: Optional[str] = None, project_id: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        results = []
        if query:
            q_lower = query.lower()
            for m in self._hot_cache:
                if q_lower in m["body"].lower(): results.append(m)
        if db is not None:
            stmt = select(Memory).order_by(desc(Memory.importance), desc(Memory.created_at))
            if agent_id: stmt = stmt.where(Memory.agent_id == agent_id)
            if category: stmt = stmt.where(Memory.category == category)
            if project_id: stmt = stmt.where(Memory.project_id == str(project_id))
            if query: stmt = stmt.where(Memory.body.ilike(f"%{query}%"))
            res = await db.execute(stmt.limit(top_k))
            for m in res.scalars().all():
                results.append({"id": str(m.id), "agent_id": m.agent_id, "body": m.body, "category": m.category, "importance": m.importance, "metadata": m.metadata_, "created_at": m.created_at.isoformat()})
        seen_ids = set()
        final_list = []
        results.sort(key=lambda x: (x.get('importance', 0), x.get('created_at', '')), reverse=True)
        for item in results:
            if item["id"] not in seen_ids:
                final_list.append(item)
                seen_ids.add(item["id"])
            if len(final_list) >= top_k: break
        return final_list

    async def search_with_causal_anchoring(self, db: AsyncSession, query: str, top_k: int = 10, use_synergy: bool = True) -> List[Dict[str, Any]]:
        primary_results = await self.search(db, query, top_k=top_k)
        return primary_results

    async def get_recent(self, db: AsyncSession, limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Sistemin en son hatıralarını döner. Rüya ve konsolidasyon için kritik."""
        stmt = select(Memory).order_by(desc(Memory.created_at))
        if category:
            stmt = stmt.where(Memory.category == category)
        
        res = await db.execute(stmt.limit(limit))
        return [{"id": str(m.id), "agent_id": m.agent_id, "body": m.body, "category": m.category, "importance": m.importance, "created_at": m.created_at.isoformat(), "metadata": m.metadata_} for m in res.scalars().all()]

    async def get_negative_patterns(self, db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
        """Negatif örüntüleri (hataları) döner."""
        stmt = select(Memory).where(Memory.category == "negative_lesson").order_by(desc(Memory.created_at))
        res = await db.execute(stmt.limit(limit))
        return [{"id": str(m.id), "body": m.body, "metadata": m.metadata_} for m in res.scalars().all()]


# Singleton
synaptic_cortex = UnifiedGalacticCortex()
ugc = synaptic_cortex
