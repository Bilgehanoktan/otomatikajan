"""
Bellek & RAG Sistemi

Saf yardımcı fonksiyonlar (_cosine_sim, _mmr) DB bağımsızdır.
Ağır bağımlılıklar yalnızca gerçekten gerektiğinde yüklenir.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from db.models import Memory


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
        from observability.logging import get_logger
        _log = get_logger("memory_store")
        _log.warning(f"Embedding API hatas (Sessizce atlanyor): {e}")
        return None


class MemoryStore:
    async def save(
        self,
        db: 'AsyncSession',
        agent_id: str,
        body: str,
        category: str = 'general',
        project_id: str | None = None,
        importance: float = 0.5,
        metadata: dict | None = None,
        tags: list | None = None,
    ) -> 'Memory':
        from db.models import Memory
        mem = Memory(
            agent_id=agent_id,
            project_id=str(project_id) if project_id else None,
            body=body,
            category=category,
            importance=importance,
            metadata_=metadata or {},
            tags=tags or []
        )
        db.add(mem)
        await db.flush()
        return mem

    # --- Katman 7: Memory and Learning Layer Core ---

    async def save_episode(self, db: 'AsyncSession', episode_data: dict) -> 'Memory':
        """Bir görevin tam yaşam döngüsünü (Episode) kaydeder."""
        metadata = dict(episode_data)
        metadata.setdefault(
            "signature",
            hashlib.sha256(
                f"episode|{metadata.get('project_id', '')}|{metadata.get('title', '')}|{metadata.get('status', '')}|{str(metadata.get('final_output', ''))[:300]}".encode('utf-8', errors='ignore')
            ).hexdigest(),
        )
        body = f"Episode: {metadata.get('title', 'Unknown')}\nResult: {metadata.get('status')}"
        return await self.save(
            db=db,
            agent_id="system",
            body=body,
            category="episode_record",
            project_id=metadata.get("project_id"),
            metadata=metadata
        )

    async def save_skill(self, db: 'AsyncSession', skill_data: dict) -> 'Memory':
        """Tekrar kullanılabilir bir yeteneği (Skill) kaydeder."""
        body = f"Skill: {skill_data.get('name')}\nDescription: {skill_data.get('description')}"
        return await self.save(
            db=db,
            agent_id="system",
            body=body,
            category="skill_artifact",
            metadata=skill_data,
            tags=["skill"]
        )

    async def save_policy(self, db: 'AsyncSession', policy_data: dict) -> 'Memory':
        """Sistem politikasını (Policy) günceller veya önerir."""
        body = f"Policy Update: {policy_data.get('title')}\nReason: {policy_data.get('reason')}"
        return await self.save(
            db=db,
            agent_id="system",
            body=body,
            category="policy_proposal",
            metadata=policy_data,
            tags=["policy"]
        )

    async def memory_write_gate(self, db: 'AsyncSession', data: Any, category: str) -> bool:
        """
        AGI Gate: Belleğe yazma izni verir.

        İlkeler:
        - Hafıza append-only kalira; veri silmek yerine yeni özet/işaretleyici eklenir.
        - Düşük değerli gürültü filtrelenir.
        - Aynı episode'un tekrar tekrar yazılması mümkün olduğunca engellenir.
        """
        importance = float(getattr(data, 'importance', 0.5) or 0.0)
        if importance < 0.3:
            return False

        verification = getattr(data, 'verification', None)
        if category == 'episode_record' and verification is not None:
            has_signal = bool(getattr(verification, 'result_status', False) or getattr(data, 'lessons_learned', []))
            if not has_signal:
                return False

        signature = self._build_memory_signature(data, category)
        if signature and db is not None:
            try:
                from sqlalchemy import select
                from db.models import Memory

                stmt = (
                    select(Memory)
                    .where(Memory.category == category)
                    .where(Memory.metadata_["signature"].astext == signature)
                    .limit(1)
                )
                existing = (await db.execute(stmt)).scalar_one_or_none()
                if existing is not None:
                    return False
            except Exception:
                # DB/JSON operatörü her ortamda hazır olmayabilir; gate'i bozmayalım.
                pass

        return True


    def _build_memory_signature(self, data: Any, category: str) -> str:
        """Aynı episode/skill/policy için kaba bir tekrar imzası üretir."""
        if category == 'episode_record':
            frame = getattr(data, 'problem_frame', None)
            verification = getattr(data, 'verification', None)
            seed = "|".join([
                category,
                getattr(frame, 'objective', '') or '',
                getattr(frame, 'task_type', None).value if getattr(frame, 'task_type', None) else '',
                str(getattr(verification, 'result_status', '')),
                str(getattr(data, 'final_output', ''))[:300],
            ])
        else:
            seed = f"{category}|{str(data)[:500]}"
        return hashlib.sha256(seed.encode('utf-8', errors='ignore')).hexdigest()

    async def save_playbook(
        self,
        db: 'AsyncSession',
        module: str,
        note: str,
        hypothesis: str
    ) -> 'Memory':
        """Faz 12.1: Tekrar kullanılabilir playbook/guardrail olarak kaydeder."""
        body = f"Guardrail/Playbook (Module: {module}):\nNote: {note}\nContext: {hypothesis}"
        return await self.save(
            db=db,
            agent_id="system",
            body=body,
            category="playbook",
            importance=0.9,
            metadata={"source": "feedback_record", "module": module}
        )
    async def get_recent(
        self,
        db: 'AsyncSession',
        category: str | None = None,
        limit: int = 10
    ) -> list['Memory']:
        """En son kaydedilen N adet bellek kaydını getirir."""
        from sqlalchemy import select
        from db.models import Memory
        stmt = select(Memory).order_by(Memory.created_at.desc()).limit(limit)
        if category:
            stmt = stmt.where(Memory.category == category)
        return (await db.execute(stmt)).scalars().all()

    async def search(
        self,
        db: 'AsyncSession',
        query: str,
        agent_id: str | None = None,
        category: str | None = None,
        project_id: str | None = None,
        top_k: int = 10,
        mmr_lambda: float = 0.7,
        token_budget: int = 2000,
    ) -> list[dict]:
        from sqlalchemy import select
        from db.models import Memory

        q_emb = await get_embedding(query)

        stmt = select(Memory)
        if agent_id:
            stmt = stmt.where(Memory.agent_id == agent_id)
        if category:
            stmt = stmt.where(Memory.category == category)
        if project_id:
            stmt = stmt.where(Memory.project_id == str(project_id))
        stmt = stmt.where((Memory.expires_at == None) | (Memory.expires_at > datetime.now(timezone.utc)))

        results = (await db.execute(stmt)).scalars().all()
        if not results:
            return []

        scored: list[tuple[Any, float, float]] = []
        for mem in results:
            vec_score = 0.0
            mem_embedding = getattr(mem, 'embedding', None)
            if q_emb is not None and mem_embedding is not None:
                vec_score = float(_cosine_sim(q_emb, mem_embedding))
            kw_score = 1.0 if any(w.lower() in mem.body.lower() for w in query.split() if len(w) > 3) else 0.0
            combined = 0.7 * vec_score + 0.3 * kw_score
            freshness = _freshness(mem.created_at)
            final = combined * (0.8 + 0.1 * getattr(mem, 'importance', 0.5) + 0.1 * freshness)
            scored.append((mem, final, vec_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        candidates = scored[:top_k * 3]
        selected = _mmr(candidates, mmr_lambda, top_k, q_emb)

        output: list[dict] = []
        used_tokens = 0
        for mem, score, vec_score in selected:
            try:
                mem.access_count += 1
            except Exception:
                pass
            approx_tokens = len(mem.body) // 4
            if used_tokens + approx_tokens > token_budget:
                break
            used_tokens += approx_tokens
            output.append({
                'id': str(mem.id),
                'agent_id': mem.agent_id,
                'category': mem.category,
                'body': mem.body,
                'score': round(score, 4),
                'vec_score': round(vec_score, 4),
                'importance': getattr(mem, 'importance', 0.5),
                'created_at': mem.created_at.isoformat(),
            })
        return output


def _cosine_sim(a: list[float], b) -> float:
    np = _np()
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom > 0 else 0.0


def _freshness(created_at: datetime) -> float:
    delta = (datetime.now(timezone.utc) - created_at).total_seconds()
    return max(0.0, 1.0 - delta / (7 * 86400))


def _mmr(candidates: list[tuple], lambda_: float, top_k: int, q_emb: list[float] | None) -> list[tuple]:
    if not q_emb or len(candidates) <= top_k:
        return candidates[:top_k]
    selected, remaining = [], list(candidates)
    while len(selected) < top_k and remaining:
        best, best_score = None, float('-inf')
        for item in remaining:
            mem, combined, _ = item
            rel = combined
            if selected and getattr(mem, 'embedding', None) is not None:
                red = max(
                    _cosine_sim(mem.embedding, s[0].embedding)
                    for s in selected
                    if getattr(s[0], 'embedding', None) is not None
                )
            else:
                red = 0.0
            mmr_score = lambda_ * rel - (1 - lambda_) * red
            if mmr_score > best_score:
                best_score, best = mmr_score, item
        if best:
            selected.append(best)
            remaining.remove(best)
    return selected


memory_store = MemoryStore()
