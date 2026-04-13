"""
Kalite Puanlayıcı — Faz 3
Her ajan çıktısını çok boyutlu değerlendirir:

  completeness   — zorunlu alanlar dolu mu?
  specificity    — belirsiz/genel mi, somut mu?
  risk_awareness — riskler ve önlemler var mı?
  actionability  — sonraki adımlar uygulanabilir mi?
  consistency    — kendi içinde çelişkisi var mı?

Sonuç: 0.0–1.0 arası float + boyut bazlı detay
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quality.output_schema import AgentOutput


# ── Vague kelimeler listesi ───────────────────────────────
VAGUE_WORDS = {
    "şey", "birşey", "birşeyler", "vs", "vb", "falan", "filan",
    "thing", "stuff", "etc", "various", "several", "some", "many",
    "maybe", "perhaps", "somehow", "something", "anything",
    "belki", "galiba", "sanırım", "gibi", "öyle", "böyle",
}

# Yüksek değerli teknik kelimeler
TECHNICAL_KEYWORDS = {
    # Mimari
    "microservice", "event-driven", "cqrs", "saga", "circuit breaker",
    "load balancer", "cache", "redis", "postgresql", "kafka", "rabbitmq",
    "serverless", "stateless", "observability", "metrics", "tracing",
    # Güvenlik
    "oauth", "jwt", "tls", "ssl", "encryption", "rate limit", "csrf", "xss",
    "sanitization", "authentication", "authorization", "rbac",
    # Test
    "unit test", "integration test", "e2e", "coverage", "mock", "fixture",
    "regression", "smoke test", "boundary test", "mutation testing",
    # DevOps
    "docker", "kubernetes", "ci/cd", "terraform", "prometheus", "grafana",
    "ansible", "helm", "infrastructure-as-code", "pipeline",
    # Kod kalitesi
    "solid", "dry", "async", "await", "transaction", "rollback", "index",
    "abstraction", "encapsulation", "polymorphism", "interface", "protocol",
    # AI & Agentic (Faz 12)
    "orchestrator", "multi-agent", "deterministic", "prompt engineering",
    "llm", "remediation", "self-healing", "autonomous", "inference",
}


@dataclass
class QualityDimension:
    name:  str
    score: float   # 0.0–1.0
    notes: list[str]


@dataclass
class QualityReport:
    overall:     float
    dimensions:  list[QualityDimension]
    passed:      bool    # overall >= 0.60 ise geçti
    feedback:    list[str]   # iyileştirme önerileri

    @property
    def total_score(self) -> float:
        return self.overall

    def to_dict(self) -> dict:
        return {
            "overall":    round(self.overall, 3),
            "passed":     self.passed,
            "dimensions": {d.name: {"score": round(d.score, 3), "notes": d.notes}
                           for d in self.dimensions},
            "feedback":   self.feedback,
        }


class QualityScorer:
    from config import QUALITY_PASS_THRESHOLD
    PASS_THRESHOLD = QUALITY_PASS_THRESHOLD   # Bu eşiğin altı reviewer'a gider

    # Boyut ağırlıkları
    WEIGHTS = {
        "completeness":   0.20,
        "specificity":    0.15,
        "risk_awareness": 0.15,
        "actionability":  0.15,
        "consistency":    0.10,
        "contract_compliance": 0.15,
        "test_sufficiency":    0.10,
    }

    def score(self, output: "AgentOutput", acceptance_criteria: list[str] = None) -> QualityReport:
        dims = [
            self._completeness(output),
            self._specificity(output),
            self._risk_awareness(output),
            self._actionability(output),
            self._consistency(output),
            self._contract_compliance(output, acceptance_criteria or []),
            self._test_sufficiency(output),
        ]

        overall = sum(
            d.score * self.WEIGHTS[d.name]
            for d in dims
        )

        feedback = []
        for d in dims:
            if d.score < 0.5:
                feedback.extend(d.notes)

        return QualityReport(
            overall=overall,
            dimensions=dims,
            passed=overall >= self.PASS_THRESHOLD,
            feedback=feedback,
        )

    # ── Boyutlar ──────────────────────────────────────────
    def _completeness(self, o: "AgentOutput") -> QualityDimension:
        notes = []
        score = 1.0

        if not o.summary or len(o.summary) < 20:
            score -= 0.3; notes.append("summary çok kısa veya yok")
        if not o.decisions:
            score -= 0.2; notes.append("hiç karar belirtilmemiş")
        if not o.next_actions:
            score -= 0.2; notes.append("sonraki adımlar eksik")
        if not o.deliverables:
            score -= 0.1; notes.append("somut çıktı tanımlanmamış")
        if o.parse_errors:
            score -= 0.1 * len(o.parse_errors); notes.append(f"{len(o.parse_errors)} parse hatası")

        return QualityDimension("completeness", max(0.0, score), notes)

    def _specificity(self, o: "AgentOutput") -> QualityDimension:
        notes = []
        all_text = " ".join([
            o.summary,
            " ".join(o.decisions),
            " ".join(o.next_actions),
            " ".join(o.quality_notes),
        ]).lower()

        word_count    = len(all_text.split())
        vague_count   = sum(1 for w in all_text.split() if w in VAGUE_WORDS)
        tech_count    = sum(1 for kw in TECHNICAL_KEYWORDS if kw in all_text)

        score = 1.0
        if word_count < 50:
            score -= 0.3; notes.append("yanıt çok kısa (< 50 kelime)")
        if vague_count > 3:
            ratio = vague_count / max(word_count, 1)
            score -= min(0.3, ratio * 5)
            notes.append(f"belirsiz ifade fazla ({vague_count} adet)")
        if tech_count == 0:
            score -= 0.2; notes.append("teknik kelime yok — çok genel")
        elif tech_count >= 3:
            score = min(1.0, score + 0.1)   # bonus

        return QualityDimension("specificity", max(0.0, score), notes)

    def _risk_awareness(self, o: "AgentOutput") -> QualityDimension:
        notes = []
        score = 1.0

        if not o.risks:
            score -= 0.4; notes.append("hiç risk belirtilmemiş")
        else:
            has_high  = any(r.severity in ("high", "critical") for r in o.risks)
            has_mitig = any(r.mitigation for r in o.risks)
            if not has_mitig:
                score -= 0.2; notes.append("risklere önlem önerilmemiş")
            if len(o.risks) == 1:
                score -= 0.1; notes.append("yalnızca 1 risk — daha kapsamlı olabilir")

        return QualityDimension("risk_awareness", max(0.0, score), notes)

    def _actionability(self, o: "AgentOutput") -> QualityDimension:
        notes = []
        score = 1.0

        actions = o.next_actions
        if not actions:
            return QualityDimension("actionability", 0.3,
                                    ["sonraki adımlar tanımlanmamış"])

        # Eylem fiili var mı? (implement, add, configure, create, test...)
        action_verbs = {
            "implement", "add", "configure", "create", "setup", "deploy",
            "test", "write", "update", "migrate", "ekle", "yaz", "oluştur",
            "konfigüre", "uygula", "test et", "deploy et", "güncelle",
        }
        verb_count = sum(
            1 for a in actions
            if any(v in a.lower() for v in action_verbs)
        )
        if verb_count == 0:
            score -= 0.3; notes.append("adımlar eylem fiili içermiyor")
        if len(actions) < 2:
            score -= 0.2; notes.append("çok az sonraki adım (< 2)")
        elif len(actions) >= 3:
            score = min(1.0, score + 0.05)

        return QualityDimension("actionability", max(0.0, score), notes)

    def _consistency(self, o: "AgentOutput") -> QualityDimension:
        """
        Kararlar ve riskler çelişiyor mu?
        Basit heuristic: teknoloji önerisi hem karar hem risk listesinde
        tamamen karşıt görünüyorsa flagle.
        """
        notes = []
        score = 1.0

        decision_text = " ".join(o.decisions).lower()
        risk_text     = " ".join(r.description for r in o.risks).lower()

        # Karar olarak önerip risk olarak da ciddi şekilde karşı çıkılan teknoloji
        tech_pattern = re.compile(r"\b(redis|kafka|postgresql|mongodb|docker|kubernetes)\b")
        dec_techs  = set(tech_pattern.findall(decision_text))
        risk_techs = set(tech_pattern.findall(risk_text))

        contested = dec_techs & risk_techs
        if len(contested) > 2:
            score -= 0.2
            notes.append(f"Aynı teknolojiler hem karar hem risk: {contested}")

        # Summary ile kararlar tamamen ayrışıyor mu?
        if o.summary and o.decisions:
            sum_words = set(o.summary.lower().split())
            dec_words = set(" ".join(o.decisions).lower().split())
            overlap   = sum_words & dec_words - {"ve", "ile", "için", "the", "a", "of"}
            if len(overlap) < 2 and len(o.decisions) > 2:
                score -= 0.1
                notes.append("summary ile kararlar arasında az örtüşme")

        return QualityDimension("consistency", max(0.0, score), notes)

    def _contract_compliance(self, o: "AgentOutput", acceptance_criteria: list[str]) -> QualityDimension:
        notes = []
        score = 1.0
        
        # Faz 12.1: Sözleşme Uyum Kontrolü
        if acceptance_criteria:
            all_text = str(o.to_dict() if hasattr(o, "to_dict") else vars(o)).lower()
            met_criteria = 0
            for crit in acceptance_criteria:
                # Basit kelime bazlı kontrol
                keywords = [w for w in crit.lower().split() if len(w) > 3]
                if not keywords or any(kw in all_text for kw in keywords):
                    met_criteria += 1
                else:
                    notes.append(f"Kriter karşınlanmamış olabilir: {crit[:50]}")
            
            if len(acceptance_criteria) > 0:
                compliance_ratio = met_criteria / len(acceptance_criteria)
                if compliance_ratio < 1.0:
                    score = compliance_ratio

        return QualityDimension("contract_compliance", max(0.0, score), notes)

    def _test_sufficiency(self, o: "AgentOutput") -> QualityDimension:
        notes = []
        score = 1.0
        
        all_text = str(o.to_dict() if hasattr(o, "to_dict") else vars(o)).lower()
        test_keywords = ["test", "pytest", "spec", "assert", "coverage", "mock"]
        
        has_tests = any(kw in all_text for kw in test_keywords)
        if not has_tests:
            score -= 0.5
            notes.append("Test veya doğrulama adımı bulunamadı")
            
        return QualityDimension("test_sufficiency", max(0.0, score), notes)


# Singleton
quality_scorer = QualityScorer()
