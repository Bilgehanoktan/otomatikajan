"""
Geliştirilmiş Bellek Erişimi — Faz 3
• DB bağımsız çalışır (pgvector yoksa keyword fallback)
• Ajan prompt'larına otomatik bağlam enjeksiyonu
• Proje bazlı bellek izolasyonu
• Öğrenme: başarılı çıktıları otomatik kaydet
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ════════════════════════════════════════════════════════
# In-memory bellek deposu (DB yoksa / test ortamında)
# ════════════════════════════════════════════════════════
@dataclass
class MemoryEntry:
    id:          str
    agent_id:    str
    category:    str
    body:        str
    importance:  float = 0.5
    project_id:  str | None = None
    metadata:    dict = field(default_factory=dict)
    access_count:int = 0
    created_at:  datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def freshness(self) -> float:
        delta = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return max(0.0, 1.0 - delta / (7 * 86400))

    def relevance_to(self, query: str) -> float:
        """Anahtar kelime benzerliği — embedding yoksa fallback."""
        q_words = set(query.lower().split())
        b_words = set(self.body.lower().split())
        if not q_words:
            return 0.0
        overlap = len(q_words & b_words)
        return min(1.0, overlap / len(q_words))


from packages.observability.memory_governor import memory_governor

class InMemoryStore:
    """Hafif in-process bellek — DB bağımlılığı yok."""

    def __init__(self, max_entries: int = 400):
        self._entries: dict[str, MemoryEntry] = {}
        self._max     = max_entries
        
        # Memory Governor'a kaydol
        memory_governor.register_cleanup_callback(self.clear_stale_entries)

    def clear_stale_entries(self):
        """Hafıza dolduğunda en az önemli %50 kaydı siler."""
        if not self._entries: return
        count = len(self._entries)
        # Önem derecesine göre sırala ve yarısını sil
        sorted_keys = sorted(self._entries, key=lambda k: self._entries[k].importance)
        for k in sorted_keys[:count // 2]:
            del self._entries[k]
        from packages.observability.logging import get_logger
        get_logger("memory_retrieval").warning(f"[MEM-STORE] Pruned {count // 2} entries.")

    def save(
        self,
        agent_id:   str,
        body:       str,
        category:   str = "general",
        project_id: str | None = None,
        importance: float = 0.5,
        metadata:   dict | None = None,
    ) -> MemoryEntry:
        entry_id = hashlib.sha256(f"{agent_id}:{body}".encode()).hexdigest()[:12]
        entry = MemoryEntry(
            id=entry_id,
            agent_id=agent_id,
            category=category,
            body=body,
            project_id=project_id,
            importance=importance,
            metadata=metadata or {},
        )
        # Kapasite aşımında en eski düşük önemli girdiyi sil
        if len(self._entries) >= self._max:
            worst = min(self._entries.values(),
                        key=lambda e: e.importance * e.freshness())
            del self._entries[worst.id]
        self._entries[entry_id] = entry
        return entry

    def search(
        self,
        query:      str,
        agent_id:   str | None = None,
        category:   str | None = None,
        project_id: str | None = None,
        top_k:      int = 8,
        token_budget: int = 2000,
    ) -> list[dict]:
        candidates = list(self._entries.values())

        # Filtrele
        if agent_id:
            candidates = [e for e in candidates if e.agent_id == agent_id]
        if category:
            candidates = [e for e in candidates if e.category == category]
        if project_id:
            candidates = [e for e in candidates if e.project_id == project_id]

        # Sırala: önem × tazelik × alaka
        scored = []
        for e in candidates:
            score = (
                0.4 * e.relevance_to(query) +
                0.3 * e.importance +
                0.3 * e.freshness()
            )
            scored.append((e, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Token bütçesi
        output, used = [], 0
        for entry, score in scored[:top_k * 2]:
            tokens = len(entry.body) // 4
            if used + tokens > token_budget:
                break
            entry.access_count += 1
            output.append({
                "id":         entry.id,
                "agent_id":   entry.agent_id,
                "category":   entry.category,
                "body":       entry.body,
                "score":      round(score, 4),
                "importance": entry.importance,
                "created_at": entry.created_at.isoformat(),
            })
            used += tokens
            if len(output) >= top_k:
                break

        return output

    def stats(self) -> dict:
        cats = {}
        for e in self._entries.values():
            cats[e.category] = cats.get(e.category, 0) + 1
        return {
            "total":      len(self._entries),
            "by_category": cats,
            "capacity":   self._max,
        }


# Singleton (DB yokken bunu kullanır)
_fallback_store = InMemoryStore(max_entries=500)


# ════════════════════════════════════════════════════════
# Reality Grounding — Gerçeklik Kontrolü (Phase 34)
# ════════════════════════════════════════════════════════
def _get_reality_context() -> str:
    """Mevcut çalışma dizinindeki dosya yapısını özetler (Daha derin bağlam)."""
    import os
    try:
        files = []
        # Faz 34: Derinlik 3'e çıkarıldı, gürültü filtreleri eklendi.
        exclude_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.gemini', '.idea'}
        
        for root, dirs, fs in os.walk(".", topdown=True):
            # Filtreleme
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            level = root.count(os.sep)
            if level > 3: continue # Depth limit (Deep Grounding)
            
            indent = "  " * level
            files.append(f"{indent}📂 {os.path.basename(root) or './'}")
            
            # Seçici dosya listeleme (Sadece önemli uzantılar)
            for f in fs[:20]: # Dosya sınırı
                if any(ext in f for ext in ['.py', '.js', '.md', '.json', '.html', '.css', '.bat', '.sh']):
                    files.append(f"{indent}  📄 {f}")
        
        return "\n".join(files)
    except Exception:
        return "Dosya listesi alınamadı."

# ════════════════════════════════════════════════════════
# Bağlam İnşaatçısı — ajan prompt'larına bellek ekler
# ════════════════════════════════════════════════════════
CONTEXT_TEMPLATE = """
=== İlgili Geçmiş Deneyimler ===
{memories}

=== Gerçeklik Bağlamı (Current FS) ===
{reality}

=== Görev ===
{task}"""


class ContextBuilder:
    """
    Ajan çalışmadan önce ilgili anıları toplar ve
    prompt'a bağlam olarak ekler.
    """

    def __init__(self, store: InMemoryStore | None = None):
        self._store = store or _fallback_store

    async def build_context(
        self,
        agent_id:   str,
        task_text:  str,
        project_id: str | None = None,
        top_k:      int = 5,
        token_budget: int = 1500,
        internal_monologue: str = ""
    ) -> str:
        """
        İlgili anıları arar, prompt'a enjekte edilecek metin döner.
        Anı yoksa orijinal görevi döner.
        """
        # Faz 39: Negatif Dersleri (Hataları) Önceliklendir
        negative_lessons = await self._search_memories(
            query=task_text,
            agent_id=agent_id,
            project_id=project_id,
            category="negative_lesson",
            top_k=3
        )
        
        memories = await self._search_memories(
            query=task_text,
            agent_id=agent_id,
            project_id=project_id,
            top_k=top_k,
            token_budget=token_budget,
        )

        mem_lines = []
        if negative_lessons:
            mem_lines.append("!!! ÖNEMLİ: GEÇMİŞ HATALARDAN DERSLER !!!")
            for i, m in enumerate(negative_lessons, 1):
                mem_lines.append(f"HATA-{i}: {m.get('body', '')}")
            mem_lines.append("-" * 30)

        if memories:
            mem_lines.append("İlgili Geçmiş Deneyimler:")
            for i, m in enumerate(memories, 1):
                cat  = m.get("category", "general")
                if cat == "negative_lesson": continue # Zaten yukarıda eklendi
                body = m.get("body", "")[:400]
                score = m.get("score", 0)
                mem_lines.append(f"{i}. [{cat}] (alaka: {score:.2f})\n   {body}")
        
        if not mem_lines or (len(mem_lines) == 1 and "Geçmiş" not in mem_lines[0]):
            mem_lines.append("İlgili geçmiş anı bulunamadı.")

        if internal_monologue:
            mem_lines.append("-" * 30)
            mem_lines.append("=== ÖNCEKİ BİLİŞSEL DÜŞÜNCE (RESUMED CONTEXT) ===")
            mem_lines.append(internal_monologue)
            mem_lines.append("-" * 30)

        reality = _get_reality_context()
        
        context = CONTEXT_TEMPLATE.format(
            memories="\n\n".join(mem_lines),
            reality=reality,
            task=task_text,
        )
        return context

    async def _search_memories(
        self,
        query:      str,
        agent_id:   str,
        project_id: str | None = None,
        category:   str | None = None,
        top_k:      int = 5,
        token_budget: int = 2000,
    ) -> list[dict]:
        # Önce DB
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store
            async with AsyncSessionLocal() as db:
                return await memory_store.search(
                    db,
                    query=query,
                    agent_id=agent_id,
                    project_id=project_id,
                    category=category,
                    top_k=top_k,
                    token_budget=token_budget,
                )
        except Exception:
            pass
        # Fallback: in-memory
        return self._store.search(
            query=query,
            agent_id=agent_id,
            project_id=project_id,
            top_k=top_k,
            token_budget=token_budget,
        )

    async def save_lesson(
        self,
        agent_id:   str,
        lesson:     str,
        category:   str = "lesson",
        project_id: str | None = None,
        importance: float = 0.7,
        db: Any | None = None,
    ):
        """Başarılı bir çıktıdan öğrenilen dersi hem DB'ye hem in-memory'ye kaydet."""
        # 1. DB'ye kaydet (kalıcı)
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store
            
            async def _persist(session):
                await memory_store.save(
                    db=session,
                    agent_id=agent_id,
                    body=lesson,
                    category=category,
                    project_id=project_id,
                    importance=importance
                )
                await session.commit()

            if db:
                await _persist(db)
            else:
                async with AsyncSessionLocal() as session:
                    await _persist(session)
        except Exception as e:
            # DB hatası kritik değil, in-memory'ye devam et
            pass

        # 2. In-memory'ye kaydet (hızlı erişim / fallback)
        self._store.save(
            agent_id=agent_id,
            body=lesson,
            category=category,
            project_id=project_id,
            importance=importance,
        )

    async def save_agent_output(
        self,
        agent_id:   str,
        output:     "Any",    # AgentOutput
        project_id: str | None = None,
        db: Any | None = None,
    ):
        """
        Kaliteli ajan çıktısını belleklere ekle:
        - summary -> lesson
        - her karar -> decision
        - her risk -> risk
        """
        if not output:
            return

        # Özet
        if hasattr(output, "summary") and output.summary:
            await self.save_lesson(
                agent_id, output.summary,
                category="summary", project_id=project_id, importance=0.6,
                db=db
            )

        # Kararlar
        for dec in getattr(output, "decisions", []):
            await self.save_lesson(
                agent_id, dec,
                category="decision", project_id=project_id, importance=0.8,
                db=db
            )

        # Riskler
        for risk in getattr(output, "risks", []):
            body = f"[{risk.severity}] {risk.description}"
            if risk.mitigation:
                body += f" -> Önlem: {risk.mitigation}"
            await self.save_lesson(
                agent_id, body,
                category="risk", project_id=project_id,
                importance=0.9 if risk.severity in ("high", "critical") else 0.6,
                db=db
            )


# Singleton
context_builder = ContextBuilder()
