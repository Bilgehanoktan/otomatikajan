"""
Patch Generator
PatchPlan -> unified diff + açıklama + risk notu

Kurallar:
- Sadece izinli dosyalara dokun
- Minimal diff — gereksiz refactor yasak
- Public API'yi sebepsiz değiştirme
- Test gerekiyorsa test de yaz
- Her diff için rationale ekle
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from repair.schemas.patch_plan import PatchPlan
from observability.logging import get_logger

_log = get_logger("repair.patch_generator")

MAX_FILE_READ = 4000  # Dosya içeriği okuma limiti


@dataclass
class GeneratedPatch:
    plan_id:         str
    diff:            str
    changed_files:   list[str] = field(default_factory=list)
    rationale:       str       = ""
    risk_notes:      str       = ""
    confidence:      int       = 0
    generated_at:    datetime  = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid(self) -> bool:
        return bool(self.diff and self.diff.strip() and "+++" in self.diff)

    def to_dict(self) -> dict:
        return {
            "plan_id":       self.plan_id,
            "diff":          self.diff,
            "changed_files": self.changed_files,
            "rationale":     self.rationale,
            "risk_notes":    self.risk_notes,
            "confidence":    self.confidence,
            "valid":         self.is_valid(),
            "generated_at":  self.generated_at.isoformat(),
        }


class PatchGenerator:
    """
    LLM'e kod bağlamı + plan vererek minimal unified diff üretir.
    """

    SYSTEM_PROMPT = """Sen kıdemli bir Staff Software Engineer olarak minimal kod yaması (patch) üretiyorsun.

TEMEL KURALLAR:
1. Sadece sana verilen hedef dosyaları değiştir — başka dosyaya dokunma
2. En küçük, en dar değişikliği yap — geniş refactor YASAK
3. Public API'yi sebepsiz değiştirme
4. Güvenlik riski oluşturma (eval, exec, path traversal, secret log)
5. Mevcut kod stilini koru
6. Değiştirmediğin satırları diff'e ekleme (@ context minimal olsun)

ÇIKTI FORMATI — sadece şunu döndür:
```diff
--- a/dosya.py
+++ b/dosya.py
@@ -satir_no,n +satir_no,n @@
 context
-eski satır
+yeni satır
 context
```

Diff sonrasına tek paragraflık RATIONALE ekle:
RATIONALE: Neden bu değişiklik yapıldı."""

    def __init__(self, model_orch=None):
        self._orch = model_orch

    async def generate(
        self,
        plan: PatchPlan,
        incident_symptom: str = "",
        stack_trace: str = "",
        project_root: str = ".",
    ) -> Optional[GeneratedPatch]:
        """
        Plan'dan patch üret. Başarısızsa None döner.
        """
        if not plan.approved:
            _log.warning(f"Plan {plan.plan_id} onaylı değil, patch üretilmedi.")
            return None

        file_contents = self._read_files(plan.target_files, project_root)
        if not file_contents:
            _log.warning(f"Plan {plan.plan_id}: hedef dosyalar okunamadı.")
            return None

        raw = await self._call_llm(plan, file_contents, incident_symptom, stack_trace)
        if not raw:
            return None

        diff, rationale = self._extract_diff_and_rationale(raw)
        if not diff:
            _log.warning(f"Plan {plan.plan_id}: diff çıkarılamadı.")
            return None

        confidence = self._score_confidence(plan, diff)
        changed    = self._extract_changed_files(diff)

        return GeneratedPatch(
            plan_id=plan.plan_id,
            diff=diff,
            changed_files=changed,
            rationale=rationale or plan.rationale,
            risk_notes=f"Risk: {plan.risk.value}. Hedef: {', '.join(plan.target_files)}",
            confidence=confidence,
        )

    def _read_files(self, files: list[str], project_root: str) -> dict[str, str]:
        contents = {}
        for f in files:
            full_path = os.path.join(project_root, f)
            if not os.path.isfile(full_path):
                continue
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                    contents[f] = fh.read(MAX_FILE_READ)
            except Exception as e:
                _log.warning(f"Dosya okunamadı {f}: {e}")
        return contents

    async def _call_llm(
        self,
        plan: PatchPlan,
        file_contents: dict[str, str],
        symptom: str,
        stack_trace: str,
    ) -> str:
        if not self._orch:
            return ""

        files_block = "\n\n".join(
            f"# {path}\n```python\n{content}\n```"
            for path, content in file_contents.items()
        )
        actions_block = "\n".join(
            f"- {a.file}: {a.change_type.value} — {a.description}"
            for a in plan.actions
        )

        prompt = (
            f"SORUN: {symptom}\n\n"
            f"STACK TRACE (kısaltılmış):\n{stack_trace[:1500]}\n\n"
            f"YAPILACAK DEĞİŞİKLİKLER:\n{actions_block}\n\n"
            f"HEDEF DOSYALAR:\n{files_block}\n\n"
            "Yukarıdaki sorunu gideren minimal unified diff üret. "
            "Sadece gerekli satırları değiştir. Başka dosyaya dokunma."
        )

        try:
            result = await self._orch.complete(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                preferred_agent="backend_dev",
                max_tokens=2000,
            )
            return result
        except Exception as e:
            _log.error(f"Patch generator LLM hatası: {e}")
            return ""

    def _extract_diff_and_rationale(self, raw: str) -> tuple[str, str]:
        """Raw LLM çıktısından diff bloğu ve rationale çıkarır."""
        diff = ""
        rationale = ""

        # Diff bloğunu çıkar
        diff_match = re.search(r"```diff\s*(.*?)```", raw, re.DOTALL)
        if diff_match:
            diff = diff_match.group(1).strip()
        else:
            # Backtick olmadan da dene
            lines = raw.split("\n")
            diff_lines = []
            in_diff = False
            for line in lines:
                if line.startswith("--- ") or line.startswith("+++ ") or line.startswith("@@ "):
                    in_diff = True
                if in_diff:
                    diff_lines.append(line)
                    if line.strip() == "" and len(diff_lines) > 5:
                        break
            if diff_lines:
                diff = "\n".join(diff_lines)

        # Rationale çıkar
        rat_match = re.search(r"RATIONALE:\s*(.+?)(?:\n\n|$)", raw, re.DOTALL)
        if rat_match:
            rationale = rat_match.group(1).strip()[:500]

        return diff, rationale

    def _extract_changed_files(self, diff: str) -> list[str]:
        """Diff'ten değişen dosya listesi çıkar."""
        matches = re.findall(r"^\+\+\+ b/(.+)$", diff, re.MULTILINE)
        return list(dict.fromkeys(matches))

    def _score_confidence(self, plan: PatchPlan, diff: str) -> int:
        """Basit confidence skoru."""
        score = 50
        if plan.approved:          score += 10
        if "+++" in diff:          score += 10
        if len(diff) < 2000:       score += 10   # minimal diff iyi işaret
        if plan.risk.value == "low": score += 20
        if plan.selected_hypothesis_confidence if hasattr(plan, "selected_hypothesis_confidence") else False:
            score += 10
        return min(score, 95)


# Singleton
_patch_generator: Optional["PatchGenerator"] = None

def get_patch_generator(model_orch=None) -> "PatchGenerator":
    global _patch_generator
    if _patch_generator is None:
        _patch_generator = PatchGenerator(model_orch)
    return _patch_generator
