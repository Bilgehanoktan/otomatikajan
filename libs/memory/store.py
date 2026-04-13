"""
Bellek & RAG Sistemi

Saf yardımcı fonksiyonlar (_cosine_sim, _mmr) DB bağımsızdır.
Ağır bağımlılıklar yalnızca gerçekten gerektiğinde yüklenir.
"""
from __future__ import annotations

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
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            'https://api.openai.com/v1/embeddings',
            headers={'Authorization': f'Bearer {api_key}'},
            json={'model': 'text-embedding-3-small', 'input': text_},
        )
        resp.raise_for_status()
        return resp.json()['data'][0]['embedding']


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
    ) -> 'Memory':
        from db.models import Memory
        # embedding = await get_embedding(body) # DB'de kolon yok, şimdilik devre dışı
        mem = Memory(
            agent_id=agent_id,
            project_id=project_id,
            body=body,
            category=category,
            importance=importance,
            metadata_=metadata or {},
        )
        db.add(mem)
        await db.flush()
        return mem

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

    async def search(
        self,
        db: 'AsyncSession',
        query: str,
        agent_id: str | None = None,
        category: str | None = None,
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
        stmt = stmt.where((Memory.expires_at == None) | (Memory.expires_at > datetime.now(timezone.utc)))

        results = (await db.execute(stmt)).scalars().all()
        if not results:
            return []

        scored: list[tuple[Any, float, float]] = []
        for mem in results:
            vec_score = 0.0
            if q_emb and getattr(mem, 'embedding', None) is not None:
                vec_score = float(_cosine_sim(q_emb, mem.embedding))
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
