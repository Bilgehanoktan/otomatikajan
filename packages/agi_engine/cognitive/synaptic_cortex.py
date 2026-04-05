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
from packages.orchestration.agi.consciousness.affective_core import affective_core

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
        """MemoryGovernor tarafından tetiklenen acil durum temizliği - V5.3 Orphan Yedekleme eklendi."""
        count = len(self._hot_cache)
        if count > 0:
            try:
                orphan_file = os.path.join(self.knowledge_dir, "orphan_memories.json")
                mode = 'a' if os.path.exists(orphan_file) else 'w'
                with open(orphan_file, mode, encoding='utf-8') as f:
                    for item in self._hot_cache:
                        f.write(json.dumps(item) + "\n")
                _log.info(f"[UGC-PRUNE] {count} orphan memory başarıyla kurtarıldı ve kalıcı depolamaya (json) aktarıldı.")
            except Exception as e:
                _log.error(f"[UGC-PRUNE] Orphan memory yedekleme hatası: {e}")
                
        self._hot_cache.clear()
        _log.warning(f"[UGC-PRUNE] Hot Cache geçici bellekten temizlendi. ({count} kayıt)")

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
        expires_at: Optional[datetime] = None,
        parent_id: Optional[uuid.UUID] = None,
        cause_id: Optional[uuid.UUID] = None
    ) -> Memory:
        """Deneyimi kaydeder ve Hot Cache'e ekler. Memory V5: Causal Anchoring."""
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
            parent_id=parent_id,
            cause_id=cause_id,
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

    async def memory_write_gate(self, db: AsyncSession, record: Any, category: str = "general") -> bool:
        """
        [FAZ 50] Bilişsel Bellek Geçidi. 
        Verinin kalıcı hafızaya (DB) yazılmaya değer olup olmadığını denetler.
        Düşük kaliteli, başarısız veya gürültülü (noisy) verilerin hafızayı kirletmesini engeller.
        """
        importance = getattr(record, "importance", 0.5)
        status = getattr(record, "status", "unknown")
        
        # Faz 50: Dinamik Eşik (Affective Core'a bağlı olabilir)
        threshold = 0.4
        
        # 1. Başarısız işler (failed) sadece 'high' severity ise kaydedilir
        if status == "error" or status == "failed":
            if importance < 0.8:
                _log.debug(f"[UGC-GATE] Kayıt reddedildi (Düşük önemde hata): {category}")
                return False

        # 2. Çok düşük önemdeki genel kayıtlar reddedilir
        if importance < threshold:
            _log.debug(f"[UGC-GATE] Kayıt reddedildi (Önem eşiği altında): {category}")
            return False

        _log.info(f"[UGC-GATE] Kayıt onaylandı: {category} (İmza: {getattr(record, 'id', 'N/A')})")
        return True

    async def save_episode(self, db: AsyncSession, episode_data: dict, parent_id: Optional[uuid.UUID] = None) -> Memory:
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
            tags=["episode", status],
            parent_id=parent_id
        )

    async def save_negative_lesson(self, db: AsyncSession, agent_id: str, body: str, importance: float = 0.7, metadata: dict = None, parent_id: Optional[uuid.UUID] = None, cause_id: Optional[uuid.UUID] = None) -> Memory:
        """Hata durumlarını ve 'yapılmaması gerekenleri' hafızaya işler. Memory V5: Causal Anchoring."""
        return await self.save(
            db=db,
            agent_id=agent_id,
            body=f"[FAILURE] {body}",
            category="negative_lesson",
            importance=importance,
            metadata=metadata or {},
            tags=["failure", "lesson"],
            parent_id=parent_id,
            cause_id=cause_id
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

    async def get_recent(self, db: AsyncSession, category: Optional[str] = None, limit: int = 10) -> List[Memory]:
        """Belirli bir kategorideki en son kayıtları getirir."""
        stmt = select(Memory).order_by(desc(Memory.created_at))
        if category:
            stmt = stmt.where(Memory.category == category)
        
        result = await db.execute(stmt.limit(limit))
        return list(result.scalars().all())

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

        # 2. DB'den ara
        db_results = []
        if db is not None:
            stmt = select(Memory).order_by(desc(Memory.importance), desc(Memory.created_at))
            if agent_id: stmt = stmt.where(Memory.agent_id == agent_id)
            if category: stmt = stmt.where(Memory.category == category)
            if project_id: stmt = stmt.where(Memory.project_id == str(project_id))
            stmt = stmt.where((Memory.expires_at == None) | (Memory.expires_at > datetime.now(timezone.utc)))
                
            if query:
                # Faz 73: Fuzzy/Keyword Search Alignment (AGI Context Recall)
                # Sadece tam eşleşme değil, kelime bazlı "Herhangi biri varsa getir" mantığı
                keywords = [k.strip() for k in query.split() if len(k) > 2]
                if keywords:
                    from sqlalchemy import or_
                    # Hem body (content) hem de metadata içinde ara
                    filters = []
                    for kw in keywords[:5]: # Performans için ilk 5 anahtar kelime
                        filters.append(Memory.body.ilike(f"%{kw}%"))
                    stmt = stmt.where(or_(*filters))
                else:
                    stmt = stmt.where(Memory.body.ilike(f"%{query}%"))
                
            result = await db.execute(stmt.limit(top_k * 2)) # Daha fazla çekip sonra harmanlıyoruz
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
        
        # 3. Birleştir ve Benzersizleştir (ID bazlı)
        seen_ids = set()
        final_list = []
        
        # Sıralama: Hem Hot Cache hem DB sonuçlarını 'importance' ve 'created_at' bazlı harmanla
        combined = results + db_results
        # ISO formatlı created_at'e göre sıralama için key
        combined.sort(key=lambda x: (x.get('importance', 0), x.get('created_at', '')), reverse=True)

        for item in combined:
            if item["id"] not in seen_ids:
                final_list.append(item)
                seen_ids.add(item["id"])
            if len(final_list) >= top_k:
                break
                
        return final_list[:top_k]

    def check_similarity(self, text_a: str, text_b: str) -> float:
        """
        Faz 12.2: Semantik Benzerlik Kontrolü.
        Basit Jaccard yerine Cosine Similarity (vektör bazlı) kullanarak kavramsal benzerliği ölçer.
        Not: API üzerinden embedding alırken gecikme olabilir, kritik looplarda dikkat edilmeli.
        """
        if not text_a or not text_b: return 0.0
        
        # Eğer çok kısaysa veya sadece bir kelimeyse basit Jaccard fallback
        if len(text_a.split()) < 3 or len(text_b.split()) < 3:
            words_a = set(text_a.lower().split())
            words_b = set(text_b.lower().split())
            if not words_a or not words_b: return 0.0
            return round(len(words_a.intersection(words_b)) / len(words_a.union(words_b)), 3)

        # Uzun metinlerde semantik karşılaştırma için asenkron yapı gerekebilir, 
        # ancak bu metod senkron imzalı. Şimdilik hızlı token-match + partial-ratio hibriti kullanıyoruz.
        # Gelecekte asenkron check_similarity_async(self, a, b) eklenebilir.
        
        from difflib import SequenceMatcher
        return round(SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio(), 3)

    async def check_semantic_similarity(self, text_a: str, text_b: str) -> float:
        """ASEM Katmanı: Gerçek vektör bazlı benzerlik."""
        emb_a = await get_embedding(text_a)
        emb_b = await get_embedding(text_b)
        
        if not emb_a or not emb_b:
            return self.check_similarity(text_a, text_b) # Fallback

        import numpy as np
        vec_a = np.array(emb_a)
        vec_b = np.array(emb_b)
        dot = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        return float(round(dot / (norm_a * norm_b), 4))

    async def follow_causal_chain(self, db: AsyncSession, root_id: uuid.UUID, limit: int = 20) -> List[Dict[str, Any]]:
        """Memory V5: Root bir nedenin tetiklediği tüm zinciri (causal trace) getirir."""
        stmt = select(Memory).where(
            (Memory.parent_id == root_id) | (Memory.cause_id == root_id)
        ).order_by(Memory.created_at.asc())
        
        result = await db.execute(stmt.limit(limit))
        rows = result.scalars().all()
        
        chain = []
        for m in rows:
            data = {
                "id": str(m.id),
                "agent_id": m.agent_id,
                "body": m.body,
                "category": m.category,
                "parent_id": str(m.parent_id) if m.parent_id else None,
                "cause_id": str(m.cause_id) if m.cause_id else None,
                "created_at": m.created_at.isoformat()
            }
            chain.append(data)
            # Recursive check for this node
            sub_chain = await self.follow_causal_chain(db, m.id, limit=limit-len(chain))
            chain.extend(sub_chain)
            if len(chain) >= limit: break
            
        return chain

    async def search_synergetic(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        [FAZ 71] Semantik Sinerji Araması (Multi-hop Knowledge Discovery). 
        Birincil arama sonuçlarından çıkarılan temalara göre ilişkili 'Bilgelik' ve 'Dersleri' de bulur.
        """
        # 1. Birincil Arama
        primary = await self.search(db, query, top_k=max(3, top_k // 2))
        if not primary: return []
        
        results = primary[:]
        seen_ids = {p["id"] for p in primary}
        
        # 2. Temaları ve Bağlamı Belirle
        # Arama sonuçlarından en önemli anahtar kelimeleri ve kategorileri topla
        extracted_tags = set()
        for p in primary:
            if p.get("metadata") and "tags" in p["metadata"]:
                for t in p["metadata"]["tags"]: extracted_tags.add(t)
            # Kategoriden de ipucu al (örn: 'database' -> 'sql')
            extracted_tags.add(p.get("category", "general"))

        # 3. İkincil Sinerjik Arama (Hop 2)
        # Sinerji için sadece yüksek önemdeki 'Bilgelik' (Wisdom) ve 'Dersleri' (Lesson) hedefliyoruz.
        synergy_queries = list(extracted_tags)[:5] # Performans için sınırla
        
        for tag in synergy_queries:
            # Her tag için bir miktar 'wisdom' ara
            synergy_hits = await self.search(
                db=db,
                query=tag,
                category="semantic_wisdom",
                top_k=2
            )
            for hit in synergy_hits:
                if hit["id"] not in seen_ids:
                    # Sinerji imzasını ekle
                    hit["body"] = f"[SYNERGY-LINK ({tag})] {hit['body']}"
                    results.append(hit)
                    seen_ids.add(hit["id"])
            
            if len(results) >= top_k: break

        # 4. Önem ve Alaka Düzeyine Göre Sırala
        results.sort(key=lambda x: x.get('importance', 0), reverse=True)
        return results[:top_k]

    async def search_with_causal_anchoring(self, db: AsyncSession, query: str, top_k: int = 10, use_synergy: bool = True) -> List[Dict[str, Any]]:
        """Daha derin bir bilişsel bağlam için semantik sonuçların causal komşularını ve sinerjik bağlarını dahil eder."""
        
        # Faz 71: Sinerji araması varsayılan olarak açık
        if use_synergy:
            primary_results = await self.search_synergetic(db, query, top_k=max(5, top_k // 2))
        else:
            primary_results = await self.search(db, query, top_k=top_k // 2)
        
        v5_context = []
        seen_ids = set()
        
        for p in primary_results:
            v5_context.append(p)
            seen_ids.add(p["id"])
            
            # Causal Tracing (Neden-Sonuç İlişkisi)
            if p.get("id"):
                try:
                    trace = await self.follow_causal_chain(db, uuid.UUID(p["id"]), limit=3)
                    for t in trace:
                        if t["id"] not in seen_ids:
                            t["body"] = f"[CAUSAL-TRACE] {t['body']}"
                            v5_context.append(t)
                            seen_ids.add(t["id"])
                except Exception as e:
                    _log.debug(f"Causal trace error on search: {e}")
        
        return v5_context[:top_k]

# Registry / Singleton Instance
ugc = UnifiedGalacticCortex()
synaptic_cortex = ugc # Backward compatibility

# Compatibility Aliases
memory_store = ugc
synaptic_memory = ugc
galaxy_cortex = ugc
