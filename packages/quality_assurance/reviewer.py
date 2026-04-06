"""
Reviewer Ajan — Faz 3
Kalite eşiğini geçemeyen ajan çıktılarını eleştirir ve revize eder.

Akış:
  Ajan çıktısı -> QualityScorer -> score < 0.60 -> ReviewerAgent
  ReviewerAgent -> LLM'e kritik soruları sor -> Revize çıktı -> yeniden parse

Maksimum 2 revizyon turu uygular; sonra en iyi skoru döner.
"""

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

# Runtime imports (TYPE_CHECKING değil)
try:
    from packages.quality_assurance.output_schema import AgentOutput as _AgentOutput
    from packages.quality_assurance.scorer import QualityReport as _QualityReport
except ImportError:
    pass


@dataclass
class ReviewResult:
    original_score:  float
    final_score:     float
    revisions:       int
    improved:        bool
    final_output:    "AgentOutput"
    review_notes:    list[str]


class ReviewerAgent:
    """
    Zayıf çıktıları otomatik revize eden meta-ajan.
    Kendi LLM çağrısını yapar; orijinal ajanın promptunu yeniden kurgulamaz,
    çıktısını eleştirir ve tamamlattırır.
    """

    MAX_REVISIONS     = 2
    IMPROVEMENT_DELTA = 0.05   # En az bu kadar iyileşmezse dur

    def __init__(self, model_orch: "ModelOrchestrator"):
        self.model_orch = model_orch

    async def review(
        self,
        output:   "AgentOutput",
        report:   "QualityReport",
        workflow_template: str = "default",
        quality_profile: str = "standard",
        acceptance_criteria: list[str] = None,
    ) -> ReviewResult:
        from packages.quality_assurance.output_schema import output_parser, OUTPUT_FORMAT_INSTRUCTION
        from packages.quality_assurance.scorer import quality_assurance_scorer

        best_output = output
        best_score  = report.overall
        review_notes: list[str] = []
        revisions = 0

        for turn in range(self.MAX_REVISIONS):
            if report.overall >= quality_scorer.PASS_THRESHOLD:
                break

            critique = self._build_critique(output, report, workflow_template, quality_profile, acceptance_criteria)
            review_notes.append(f"Tur {turn+1}: {critique[:120]}")

            try:
                revised_raw = await asyncio.wait_for(
                    self.model_orch.complete(
                        messages=[{"role": "user", "content": critique}],
                        max_tokens=900,
                    ),
                    timeout=30.0,
                )
                revisions += 1

                revised_output = output_parser.parse(output.agent_id, revised_raw)
                revised_report = quality_scorer.score(revised_output)

                if revised_report.overall >= best_score + self.IMPROVEMENT_DELTA:
                    best_output = revised_output
                    best_score  = revised_report.overall
                    report      = revised_report
                    output      = revised_output
                    review_notes.append(
                        f"  -> İyileşti: {best_score:.2f} (+{revised_report.overall - report.overall:.2f})"
                    )
                else:
                    review_notes.append(f"  -> İyileşme yok ({revised_report.overall:.2f}), duruyorum.")
                    break

            except asyncio.TimeoutError:
                review_notes.append(f"  -> Revizyon zaman aşımı")
                break
            except Exception as e:
                review_notes.append(f"  -> Revizyon hatası: {e}")
                break

        return ReviewResult(
            original_score = report.overall if revisions == 0 else (
                quality_scorer.score(output).overall
            ),
            final_score    = best_score,
            revisions      = revisions,
            improved       = best_score > report.overall + self.IMPROVEMENT_DELTA,
            final_output   = best_output,
            review_notes   = review_notes,
        )

    def _build_critique(
        self,
        output: "AgentOutput",
        report: "QualityReport",
        workflow_template: str = "default",
        quality_profile: str = "standard",
        acceptance_criteria: list[str] = None,
    ) -> str:
        """Reviewer prompt'u oluştur."""
        weak_dims = [
            f"- {d.name}: {d.score:.0%} — {', '.join(d.notes)}"
            for d in report.dimensions
            if d.score < 0.6
        ]
        weak_str = "\n".join(weak_dims) if weak_dims else "Genel olarak zayıf"

        from packages.quality_assurance.output_schema import OUTPUT_FORMAT_INSTRUCTION as _FMT
        return (
            f"Sen kıdemli bir yazılım mühendisisin ve aşağıdaki ajan yanıtını eleştiriyorsun.\n\n"
            f"== Mevcut Ajan Yanıtı ({output.agent_id}) ==\n"
            f"Özet: {output.summary[:300]}\n"
            f"Kararlar: {output.decisions[:3]}\n"
            f"Riskler: {[r.description for r in output.risks[:2]]}\n"
            f"Sonraki adımlar: {output.next_actions[:3]}\n\n"
            f"== Kalite Sorunları ==\n{weak_str}\n\n"
            f"== Proje Bağlamı ==\n"
            f"İş Akışı Şablonu: {workflow_template}\n"
            f"Kalite Profili: {quality_profile}\n"
            f"Kabul Kriterleri: {acceptance_criteria or 'Belirtilmedi'}\n\n"
            f"== Görev ==\n"
            f"Yukarıdaki yanıtı şu eksiklikleri gidererek tamamen yeniden yaz.\n"
            f"Özellikle:\n{self._targeted_instructions(report)}\n\n"
            f"{_FMT}"
        )

    def _targeted_instructions(self, report: "QualityReport") -> str:
        instructions = []
        for d in report.dimensions:
            if d.score < 0.5:
                instr = {
                    "completeness":   "- Tüm alanları doldur: kararlar, riskler, çıktılar, sonraki adımlar",
                    "specificity":    "- Belirsiz ifadeler yerine somut teknoloji/araç/yaklaşım adları kullan",
                    "risk_awareness": "- En az 3 risk listele, her biri için önlem öner",
                    "actionability":  "- Sonraki adımlar eylem fiili ile başlasın (implement, add, create...)",
                    "consistency":    "- Kararlar ve riskler birbiriyle tutarlı olsun",
                }.get(d.name, f"- {d.name} boyutunu iyileştir")
                instructions.append(instr)
        return "\n".join(instructions) if instructions else "- Genel kaliteyi artır"
