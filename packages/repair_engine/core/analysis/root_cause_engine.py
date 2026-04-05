"""
Root Cause Analysis Engine
DiagnosisTicket + kod bağlamı -> RootCauseHypothesis listesi + seçim

Akış:
1. Repo bağlamını oku (suspect files içeriği)
2. LLM'e minimum 3 hipotez üret
3. Kanıt karşılaştır
4. En yüksek confidence'ı seç
5. Güven çok düşükse manual_review_only öner
"""

import os
from typing import Optional

from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, RootCauseHypothesis, RepairMode
from packages.observability.logging import get_logger

_log = get_logger("repair.root_cause")

# Güven eşiği — bunun altıysa manual review
_MIN_CONFIDENCE_FOR_AUTO_PATCH = 60


class RepoContextBuilder:
    """Şüpheli dosyaları okuyup LLM için bağlam oluşturur."""

    MAX_FILE_CHARS = 3000   # dosya başına karakter limiti

    def build(self, candidate_files: list[str], project_root: str = ".") -> str:
        parts: list[str] = []
        for rel_path in candidate_files[:5]:   # max 5 dosya
            full_path = os.path.join(project_root, rel_path)
            if not os.path.isfile(full_path):
                parts.append(f"# [{rel_path}] — dosya bulunamadı")
                continue
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(self.MAX_FILE_CHARS)
                parts.append(f"# [{rel_path}]\n{content}")
            except Exception as e:
                parts.append(f"# [{rel_path}] — okunamadı: {e}")
        return "\n\n".join(parts)


class RootCauseEngine:
    """
    LLM destekli kök neden analizi.
    Minimum 3 hipotez üretir, kanıt karşılaştırır, seçer.
    """

    SYSTEM_PROMPT = """Sen kıdemli bir Staff Software Architect ve Reliability Engineer'sın.
Sana bir yazılım incident'i, ilgili stack trace ve şüpheli dosya içerikleri verilecek.

Görevin:
1. En az 3 farklı kök neden hipotezi üret (her biri farklı açıdan yaklaşmalı)
2. Her hipotez için: başlık, açıklama, destekleyen kanıtlar, zayıflatan kanıtlar, güven skoru (0-100)
3. En olası kök nedeni seç

KURALLARI:
- Asla tahmin ettiğini söyleme, kanıta dayan
- Eğer kanıt yetersizse confidence düşük tut
- Auth / security sorunlarında confidence ne kadar yüksek olursa olsun "requires_human: true" koy
- Yanıtı JSON formatında ver

JSON FORMAT:
{
  "hypotheses": [
    {
      "id": "H1",
      "title": "Kısa başlık",
      "explanation": "Teknik açıklama",
      "supporting_evidence": ["kanıt 1", "kanıt 2"],
      "contradicting_evidence": ["zayıflatan 1"],
      "confidence": 85
    }
  ],
  "selected_id": "H1",
  "rationale": "Neden bu seçildi",
  "requires_human": false,
  "overall_confidence": 85
}"""

    def __init__(self, model_orch=None):
        self._orch = model_orch
        self._ctx_builder = RepoContextBuilder()

    async def analyze(
        self,
        ticket: DiagnosisTicket,
        incident_symptom: str,
        stack_trace: str,
        project_root: str = ".",
    ) -> DiagnosisTicket:
        """
        Ticket'e hipotezler + seçilen hipotez ekler.
        Orijinal ticket'i in-place günceller ve döner.
        """
        repo_ctx = self._ctx_builder.build(ticket.candidate_files, project_root)
        result   = await self._call_llm(incident_symptom, stack_trace, repo_ctx)
        self._apply_result(ticket, result)
        return ticket

    async def _call_llm(self, symptom: str, stack_trace: str, repo_ctx: str) -> dict:
        """LLM'den JSON hipotez listesi al."""
        if not self._orch:
            return self._fallback_analysis(symptom, stack_trace)

        prompt = (
            f"INCIDENT: {symptom}\n\n"
            f"STACK TRACE:\n{stack_trace[:3000]}\n\n"
            f"KOD BAĞLAMI:\n{repo_ctx[:4000]}\n\n"
            "Yukarıdaki incident için kök neden analizi yap. JSON formatında yanıt ver."
        )
        try:
            raw = await self._orch.complete(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                preferred_agent="architect",
                max_tokens=1500,
            )
            import json, re
            # JSON bloğunu çıkar
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            _log.warning(f"Root cause LLM çağrısı başarısız: {e}")

        return self._fallback_analysis(symptom, stack_trace)

    def _fallback_analysis(self, symptom: str, stack_trace: str) -> dict:
        """LLM yoksa kural tabanlı basit analiz."""
        hypotheses = []
        idx = 1

        checks = [
            ("ImportError" in stack_trace or "ModuleNotFoundError" in stack_trace,
             "Eksik Import", "Modül veya sembol import edilmemiş.", ["stack trace'de ImportError var"], [], 80),
            ("AttributeError" in stack_trace or "has no attribute" in stack_trace,
             "Tip/Kontrat Uyumsuzluğu", "Beklenen attribute veya metot bulunamadı.", ["AttributeError gözlemlendi"], [], 70),
            ("NoneType" in stack_trace or "is None" in stack_trace,
             "None Referans Hatası", "Beklenen değer None döndü.", ["NoneType stack trace'de"], [], 65),
            (True,
             "Bağlam Yetersiz", "Stack trace analizi ile net tespit yapılamadı.", [], ["kanıt eksik"], 20),
        ]

        for condition, title, explanation, sup, con, conf in checks:
            if condition:
                hypotheses.append({
                    "id": f"H{idx}",
                    "title": title,
                    "explanation": explanation,
                    "supporting_evidence": sup,
                    "contradicting_evidence": con,
                    "confidence": conf,
                })
                idx += 1
                if len(hypotheses) >= 3:
                    break

        best = max(hypotheses, key=lambda h: h["confidence"]) if hypotheses else {"id": "H1"}
        return {
            "hypotheses":        hypotheses,
            "selected_id":       best.get("id", "H1"),
            "rationale":         "Kural tabanlı otomatik analiz (LLM yok).",
            "requires_human":    best.get("confidence", 0) < _MIN_CONFIDENCE_FOR_AUTO_PATCH,
            "overall_confidence": best.get("confidence", 0),
        }

    def _apply_result(self, ticket: DiagnosisTicket, result: dict):
        """LLM sonucunu ticket'e uygula."""
        hypotheses_raw = result.get("hypotheses", [])
        ticket.hypotheses = [
            RootCauseHypothesis(
                id=h.get("id", "H?"),
                title=h.get("title", ""),
                explanation=h.get("explanation", ""),
                supporting_evidence=h.get("supporting_evidence", []),
                contradicting_evidence=h.get("contradicting_evidence", []),
                confidence=h.get("confidence", 0),
            )
            for h in hypotheses_raw
        ]

        selected_id = result.get("selected_id")
        if selected_id:
            for h in ticket.hypotheses:
                if h.id == selected_id:
                    ticket.selected_hypothesis = h
                    break

        overall = result.get("overall_confidence", 0)
        requires_human = result.get("requires_human", True)

        # Güven düşükse veya insan gerekiyorsa modu güncelle
        if requires_human or overall < _MIN_CONFIDENCE_FOR_AUTO_PATCH:
            ticket.recommended_mode = RepairMode.MANUAL_ONLY
            ticket.requires_human   = True
        
        if result.get("rationale"):
            ticket.rationale += f" | LLM: {result['rationale'][:200]}"


# Singleton — main.py'de inject edilir
_root_cause_engine: Optional["RootCauseEngine"] = None

def get_root_cause_engine(model_orch=None) -> "RootCauseEngine":
    global _root_cause_engine
    if _root_cause_engine is None:
        _root_cause_engine = RootCauseEngine(model_orch)
    return _root_cause_engine
