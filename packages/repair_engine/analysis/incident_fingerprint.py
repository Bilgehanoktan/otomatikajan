"""
Incident Fingerprint & Similarity Engine — Faz 11

Duplicate ve benzer incident'leri tespit eder.
  - Hash tabanlı exact match
  - String similarity fuzzy match
  - Normalized stack trace karşılaştırması
"""
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from packages.repair_engine.schemas.incident import IncidentRecord
from packages.observability.logging import get_logger

_log = get_logger("repair.analysis.fingerprint")


# ── Normalizer ────────────────────────────────────────────────

def _normalize_stack_trace(stack: str) -> str:
    """Stack trace'den dinamik değerleri temizle: satır no, memory adresi, UUID, timestamp."""
    s = stack
    s = re.sub(r"line \d+", "line N", s)
    s = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", s)
    s = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "UUID", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "TIMESTAMP", s)
    s = re.sub(r"\b\d+\b", "N", s)
    return s.strip()


def _normalize_symptom(symptom: str) -> str:
    """Symptom'dan dinamik değerleri temizle."""
    s = symptom.lower()
    s = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "UUID", s)
    s = re.sub(r"\b\d+\b", "N", s)
    s = re.sub(r"'[^']{1,40}'", "'STR'", s)
    return s.strip()


def _extract_error_type(stack: str, symptom: str) -> str:
    """Stack veya symptom'dan hata tipini çıkar."""
    patterns = [
        r"(NameError|TypeError|ValueError|AttributeError|ImportError|"
        r"ModuleNotFoundError|KeyError|IndexError|RuntimeError|"
        r"AssertionError|NotImplementedError|PermissionError|"
        r"FileNotFoundError|ConnectionError|TimeoutError)",
    ]
    for p in patterns:
        m = re.search(p, stack + " " + symptom)
        if m:
            return m.group(1)
    if "404" in symptom or "not found" in symptom.lower():
        return "NotFoundError"
    if "500" in symptom:
        return "InternalServerError"
    return "UnknownError"


# ── Fingerprint ───────────────────────────────────────────────

@dataclass
class IncidentFingerprint:
    """Bir incident'in karşılaştırılabilir parmak izi."""
    incident_id:    str
    exact_hash:     str       # SHA256 — exact duplicate tespiti
    fuzzy_key:      str       # Normalize edilmiş arama anahtarı
    error_type:     str
    module:         str
    top_frames:     list[str] = field(default_factory=list)  # İlk 3 stack frame
    symptom_norm:   str = ""
    created_at:     datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "incident_id":  self.incident_id,
            "exact_hash":   self.exact_hash,
            "error_type":   self.error_type,
            "module":       self.module,
            "top_frames":   self.top_frames,
            "symptom_norm": self.symptom_norm,
        }


def build_fingerprint(incident: IncidentRecord) -> IncidentFingerprint:
    """IncidentRecord -> IncidentFingerprint üret."""
    norm_stack   = _normalize_stack_trace(incident.stack_trace)
    norm_symptom = _normalize_symptom(incident.symptom)
    error_type   = _extract_error_type(incident.stack_trace, incident.symptom)

    # Top 3 frame (sınıf/fonksiyon isimleri)
    frames = re.findall(r'File "([^"]+)", line \d+, in (\w+)', incident.stack_trace)
    top_frames = [f"{os.path.basename(f)}:{fn}" for f, fn in frames[:3]] if frames else []

    # Exact hash: error_type + module + normalized stack (ilk 500 char)
    raw = f"{error_type}|{incident.module}|{norm_stack[:500]}"
    exact_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    # Fuzzy key: error_type + module + symptom normalize
    fuzzy_key = f"{error_type}:{incident.module}:{norm_symptom[:100]}"

    return IncidentFingerprint(
        incident_id=incident.incident_id,
        exact_hash=exact_hash,
        fuzzy_key=fuzzy_key,
        error_type=error_type,
        module=incident.module,
        top_frames=top_frames,
        symptom_norm=norm_symptom,
    )


import os  # noqa: E402 (used in build_fingerprint)


# ── Similarity Engine ─────────────────────────────────────────

@dataclass
class SimilarIncident:
    incident_id:    str
    similarity:     float   # 0.0–1.0
    match_type:     str     # "exact" | "module_error" | "fuzzy_symptom"
    reason:         str


class IncidentSimilarityEngine:
    """
    Mevcut fingerprint havuzunda benzer incident arar.
    Üç seviye kontrol:
      1. exact_hash eşleşmesi -> aynı hata
      2. module + error_type eşleşmesi -> aynı modülden aynı tip hata
      3. Symptom Jaccard benzerliği -> benzer açıklama
    """

    def __init__(self):
        self._fingerprints: dict[str, IncidentFingerprint] = {}

    def add(self, fp: IncidentFingerprint) -> None:
        self._fingerprints[fp.incident_id] = fp

    def find_similar(
        self,
        fp: IncidentFingerprint,
        limit: int = 5,
        min_similarity: float = 0.5,
    ) -> list[SimilarIncident]:
        results: list[SimilarIncident] = []
        for other_id, other in self._fingerprints.items():
            if other_id == fp.incident_id:
                continue

            # Seviye 1: exact hash
            if other.exact_hash == fp.exact_hash:
                results.append(SimilarIncident(
                    incident_id=other_id,
                    similarity=1.0,
                    match_type="exact",
                    reason=f"Aynı hata parmak izi (hash={fp.exact_hash})",
                ))
                continue

            # Seviye 2: module + error_type
            if other.module == fp.module and other.error_type == fp.error_type:
                score = 0.75
                # Frame overlap bonus
                if fp.top_frames and other.top_frames:
                    common = set(fp.top_frames) & set(other.top_frames)
                    score += 0.1 * len(common)
                results.append(SimilarIncident(
                    incident_id=other_id,
                    similarity=min(score, 0.95),
                    match_type="module_error",
                    reason=f"{fp.module} modülünde {fp.error_type} tekrarı",
                ))
                continue

            # Seviye 3: symptom Jaccard
            sim = _jaccard(fp.symptom_norm, other.symptom_norm)
            if sim >= min_similarity:
                results.append(SimilarIncident(
                    incident_id=other_id,
                    similarity=sim,
                    match_type="fuzzy_symptom",
                    reason=f"Benzer semptom (Jaccard={sim:.2f})",
                ))

        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:limit]

    def is_duplicate(self, fp: IncidentFingerprint) -> Optional[str]:
        """Exact duplicate varsa incident_id döndür, yoksa None."""
        for other_id, other in self._fingerprints.items():
            if other_id != fp.incident_id and other.exact_hash == fp.exact_hash:
                return other_id
        return None

    def stats(self) -> dict:
        return {
            "total_fingerprints": len(self._fingerprints),
            "unique_modules":     len({fp.module for fp in self._fingerprints.values()}),
            "unique_error_types": len({fp.error_type for fp in self._fingerprints.values()}),
        }


def _jaccard(a: str, b: str) -> float:
    """İki string arasında token-based Jaccard benzerliği."""
    if not a or not b:
        return 0.0
    sa, sb = set(a.split()), set(b.split())
    inter  = sa & sb
    union  = sa | sb
    return len(inter) / len(union) if union else 0.0


# Singleton
_similarity_engine = IncidentSimilarityEngine()


def get_similarity_engine() -> IncidentSimilarityEngine:
    return _similarity_engine
