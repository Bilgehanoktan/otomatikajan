"""
VectorLessonsStore — pgvector Tabanlı Deneyim Hafızası (Faz 12)

Her başarıyla çözülen incident'in semptom + çözüm özetini
embedding vektörü ile depolar. Yeni incident geldiğinde
cosine similarity ile benzer geçmiş çözümleri bulur (RAG).

Fallback: pgvector/DB yoksa in-memory TF-IDF benzeri yaklaşım kullanır.
"""

import json
import math
import os
import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from packages.observability.logging import get_logger

_log = get_logger("repair.memory.vector_lessons")


@dataclass
class VectorLesson:
    lesson_id:   str
    symptom:     str
    module:      str
    resolution:  str          # Başarılı çözüm özeti / patch açıklaması
    job_id:      str
    incident_id: str
    embedding:   list[float]  = field(default_factory=list)
    created_at:  float        = field(default_factory=time.time)
    tags:        list[str]    = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "lesson_id":   self.lesson_id,
            "symptom":     self.symptom[:200],
            "module":      self.module,
            "resolution":  self.resolution[:300],
            "job_id":      self.job_id,
            "incident_id": self.incident_id,
            "tags":        self.tags,
            "created_at":  self.created_at,
        }


@dataclass
class SimilarLesson:
    lesson:     VectorLesson
    score:      float    # 0.0-1.0 benzerlik
    match_type: str      # "vector" | "tfidf" | "keyword"


# ── TF-IDF benzeri in-memory embedding ────────────────────────
def _tokenize(text: str) -> list[str]:
    """Basit tokenizer — küçük harf, alfanumerik."""
    return re.findall(r"[a-z0-9_]{2,}", text.lower())


def _tfidf_vector(tokens: list[str], vocab: dict[str, int]) -> list[float]:
    """Kelime frekansına dayalı sparse vektör."""
    counts = Counter(tokens)
    total  = sum(counts.values()) or 1
    vec    = [0.0] * len(vocab)
    for tok, cnt in counts.items():
        if tok in vocab:
            vec[vocab[tok]] = cnt / total
    return vec


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Cosine similarity — sıfır vektör koruması ile."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot  = sum(x * y for x, y in zip(a, b))
    na   = math.sqrt(sum(x * x for x in a))
    nb   = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorLessonsStore:
    """
    Deneyim hafızası.

    save_lesson()  -> başarılı onarım sonrası çağrılır
    find_similar() -> yeni incident geldiğinde geçmiş çözümleri getirir

    pgvector bağlantısı yoksa in-memory TF-IDF ile çalışır.
    """

    def __init__(self, use_db: bool = True):
        self._use_db  = use_db
        self._lessons: list[VectorLesson]     = []  # in-memory fallback
        self._vocab:   dict[str, int]         = {}  # TF-IDF vocab

    # ── Public API ──────────────────────────────────────────────

    def save_lesson(
        self,
        symptom:    str,
        module:     str,
        resolution: str,
        job_id:     str,
        incident_id: str,
        tags:       Optional[list[str]] = None,
    ) -> VectorLesson:
        """Başarılı onarımı hafızaya kaydet."""
        text     = f"{symptom} {module} {resolution}"
        tokens   = _tokenize(text)
        embedding = self._build_embedding(tokens)

        lesson = VectorLesson(
            lesson_id   = f"vl_{uuid.uuid4().hex[:8]}",
            symptom     = symptom,
            module      = module,
            resolution  = resolution,
            job_id      = job_id,
            incident_id = incident_id,
            embedding   = embedding,
            tags        = tags or [],
        )
        self._lessons.append(lesson)
        _log.info(
            f"Vector lesson kaydedildi: {lesson.lesson_id} "
            f"module={module} | {len(self._lessons)} toplam ders"
        )

        # DB'ye kaydet (varsa)
        if self._use_db:
            self._save_to_db(lesson)
        
        # Disk yedeği
        self.save_to_disk()

        return lesson

    def find_similar(
        self,
        symptom:      str,
        module:       str = "",
        limit:        int = 3,
        min_score:    float = 0.25,
        prefer_module: bool = True,
    ) -> list[SimilarLesson]:
        """
        Yeni incident için benzer geçmiş çözümleri bul.

        Args:
            symptom:       Yeni incident semptomu
            module:        Modül filtresi (boşsa tüm modüller)
            limit:         Maksimum sonuç sayısı
            min_score:     Minimum benzerlik eşiği
            prefer_module: Aynı modülden çözümlere bonus ver
        """
        if not self._lessons:
            return []

        query_tokens = _tokenize(f"{symptom} {module}")
        q_embedding  = self._build_embedding(query_tokens)

        results: list[SimilarLesson] = []
        for lesson in self._lessons:
            score = _cosine_sim(q_embedding, lesson.embedding)

            # Aynı modül bonusu
            if prefer_module and module and lesson.module == module:
                score = min(score + 0.2, 1.0)

            if score >= min_score:
                results.append(SimilarLesson(
                    lesson=lesson,
                    score=round(score, 3),
                    match_type="tfidf",
                ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def find_similar_by_module(self, module: str, limit: int = 5) -> list[VectorLesson]:
        """Aynı modülden tüm geçmiş çözümleri döndür."""
        return [l for l in self._lessons if l.module == module][:limit]

    def stats(self) -> dict:
        from collections import Counter
        if not self._lessons:
            return {"total": 0}
        modules = Counter(l.module for l in self._lessons)
        return {
            "total":       len(self._lessons),
            "vocab_size":  len(self._vocab),
            "top_modules": dict(modules.most_common(5)),
        }

    def export(self) -> list[dict]:
        return [l.to_dict() for l in self._lessons]

    # ── İç Metodlar ─────────────────────────────────────────────

    def _build_embedding(self, tokens: list[str]) -> list[float]:
        """Vocab'ı güncelle ve TF-IDF embedding üret."""
        for tok in tokens:
            if tok not in self._vocab:
                self._vocab[tok] = len(self._vocab)

        current_dim = len(self._vocab)
        for lesson in self._lessons:
            if len(lesson.embedding) < current_dim:
                lesson.embedding.extend([0.0] * (current_dim - len(lesson.embedding)))

        embedding = _tfidf_vector(tokens, self._vocab)
        while len(embedding) < current_dim:
            embedding.append(0.0)
        return embedding

    def _save_to_db(self, lesson: VectorLesson) -> None:
        """DB'ye asenkron kaydet."""
        try:
            import asyncio
            asyncio.create_task(self._async_save_to_db(lesson))
        except Exception as e:
            _log.debug(f"DB kayıt başlatma hatası: {e}")

    async def _async_save_to_db(self, lesson: VectorLesson) -> None:
        try:
            from packages.persistence.session import AsyncSessionLocal, is_db_available
            if not await is_db_available(): return
            from packages.persistence.repair_models import VectorLessonModel
            async with AsyncSessionLocal() as db:
                model = VectorLessonModel(
                    lesson_id=lesson.lesson_id,
                    symptom=lesson.symptom,
                    module=lesson.module,
                    resolution=lesson.resolution,
                    job_id=lesson.job_id,
                    incident_id=lesson.incident_id,
                    embedding=lesson.embedding,
                    tags=lesson.tags
                )
                db.add(model)
                await db.commit()
                _log.debug(f"Vector lesson DB'ye yazıldı: {lesson.lesson_id}")
        except Exception as e:
            _log.warning(f"Vector lesson DB yazma hatası: {e}")

    async def load_from_db(self) -> None:
        """Başlangıçta DB'deki dersleri yükle."""
        try:
            from packages.persistence.session import AsyncSessionLocal, is_db_available
            if not await is_db_available(): return
            from packages.persistence.repair_models import VectorLessonModel
            from sqlalchemy import select
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(VectorLessonModel))
                rows = result.scalars().all()
                loaded_ids = {l.lesson_id for l in self._lessons}
                for row in rows:
                    if row.lesson_id in loaded_ids: continue
                    lesson = VectorLesson(
                        lesson_id=row.lesson_id,
                        symptom=row.symptom,
                        module=row.module,
                        resolution=row.resolution,
                        job_id=row.job_id,
                        incident_id=row.incident_id,
                        embedding=row.embedding or [],
                        tags=row.tags or []
                    )
                    self._lessons.append(lesson)
                _log.info(f"DB'den {len(rows)} vector lesson yüklendi.")
        except Exception as e:
            _log.error(f"Vector lesson yükleme hatası: {e}")

    def save_to_disk(self, path: str = "workspace/repair_lessons.json") -> bool:
        """Dersleri diske yedekle (JSON)."""
        try:
            data = [l.to_dict() for l in self._lessons]
            # embedding'leri de saklayalım (opsiyonel ama tutarlılık için iyi)
            for i, l in enumerate(self._lessons):
                data[i]["embedding"] = l.embedding
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            _log.error(f"Vector lesson disk yazma hatası: {e}")
            return False

    def load_from_disk(self, path: str = "workspace/repair_lessons.json") -> bool:
        """Diskten dersleri yükle."""
        if not os.path.exists(path): return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            loaded_ids = {l.lesson_id for l in self._lessons}
            for d in data:
                if d["lesson_id"] in loaded_ids: continue
                lesson = VectorLesson(
                    lesson_id=d["lesson_id"],
                    symptom=d["symptom"],
                    module=d["module"],
                    resolution=d["resolution"],
                    job_id=d["job_id"],
                    incident_id=d["incident_id"],
                    embedding=d.get("embedding", []),
                    tags=d.get("tags", []),
                    created_at=d.get("created_at", time.time())
                )
                self._lessons.append(lesson)
            _log.info(f"Diskten {len(data)} vector lesson yüklendi.")
            return True
        except Exception as e:
            _log.error(f"Vector lesson disk okuma hatası: {e}")
            return False


# Singleton
_vector_lessons: "VectorLessonsStore | None" = None


def get_vector_lessons(use_db: bool = True) -> VectorLessonsStore:
    global _vector_lessons
    if _vector_lessons is None:
        _vector_lessons = VectorLessonsStore(use_db=use_db)
    return _vector_lessons
