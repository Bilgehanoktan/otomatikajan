"""
Ajan Çıktı Şeması — Faz 3
Her ajan serbestçe metin yazmak yerine bu yapıyı döndürür.
Böylece: sentez, kalite skoru, hafıza kaydı, dashboard kolay olur.

Şema:
  summary        — 1-2 cümle özet (zorunlu)
  decisions      — verilen teknik kararlar listesi
  assumptions    — yapılan varsayımlar
  risks          — tespit edilen riskler (severity ile)
  deliverables   — somut çıktılar (kod, döküman, config vb.)
  next_actions   — sonraki adımlar
  quality_notes  — kalite / test notları
  raw_response   — LLM'in ham yanıtı (kayıt için)
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    tool_name: str
    tool_input: Dict[str, Any]


class RiskSeverity(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    CRITICAL = "critical"


@dataclass
class Risk:
    description: str
    severity:    RiskSeverity = RiskSeverity.MEDIUM
    mitigation:  str          = ""


@dataclass
class Deliverable:
    type:        str    # "code" | "config" | "doc" | "design" | "test" | "other"
    name:        str
    description: str
    content:     str = ""   # varsa gerçek içerik


@dataclass
class AgentOutput:
    agent_id:     str
    summary:      str
    decisions:    list[str]       = field(default_factory=list)
    assumptions:  list[str]       = field(default_factory=list)
    risks:        list[Risk]      = field(default_factory=list)
    deliverables: list[Deliverable] = field(default_factory=list)
    next_actions: list[str]       = field(default_factory=list)
    quality_notes:list[str]       = field(default_factory=list)
    raw_response: str             = ""
    parse_errors: list[str]       = field(default_factory=list)

    # Kalite skoru (QualityScorer tarafından doldurulur)
    quality_score:  float | None  = None
    quality_detail: dict          = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_id":      self.agent_id,
            "summary":       self.summary,
            "decisions":     self.decisions,
            "assumptions":   self.assumptions,
            "risks":         [{"desc": r.description, "severity": r.severity,
                                "mitigation": r.mitigation} for r in self.risks],
            "deliverables":  [{"type": d.type, "name": d.name,
                                "desc": d.description} for d in self.deliverables],
            "next_actions":  self.next_actions,
            "quality_notes": self.quality_notes,
            "quality_score": self.quality_score,
            "quality_detail":self.quality_detail,
            "parse_errors":  self.parse_errors,
        }

    def to_markdown(self) -> str:
        """Dashboard ve rapor için insan okunabilir format."""
        lines = [f"### {self.agent_id.upper()} Çıktısı\n"]
        lines.append(f"**Özet:** {self.summary}\n")

        if self.decisions:
            lines.append("**Kararlar:**")
            lines.extend(f"- {d}" for d in self.decisions)
            lines.append("")

        if self.risks:
            lines.append("**Riskler:**")
            for r in self.risks:
                icon = {"low": "🟢", "medium": "🟡", "high": "🔴", "critical": "🚨"}.get(r.severity, "⚪")
                lines.append(f"- {icon} [{r.severity.upper()}] {r.description}")
                if r.mitigation:
                    lines.append(f"  -> Önlem: {r.mitigation}")
            lines.append("")

        if self.deliverables:
            lines.append("**Çıktılar:**")
            lines.extend(f"- [{d.type}] **{d.name}**: {d.description}" for d in self.deliverables)
            lines.append("")

        if self.next_actions:
            lines.append("**Sonraki Adımlar:**")
            lines.extend(f"- {a}" for a in self.next_actions)
            lines.append("")

        if self.quality_score is not None:
            lines.append(f"**Kalite Skoru:** {self.quality_score:.0%}")

        return "\n".join(lines)


# ════════════════════════════════════════════════════════
# Prompt Şablonu — LLM'e verilecek çıktı formatı talimatı
# ════════════════════════════════════════════════════════
OUTPUT_FORMAT_INSTRUCTION = """
Yanıtını aşağıdaki JSON şemasında ver. Başka bir şey yazma.

{
  "summary": "1-2 cümle özet",
  "decisions": ["karar1", "karar2"],
  "assumptions": ["varsayım1"],
  "risks": [
    {"description": "risk açıklaması", "severity": "low|medium|high|critical", "mitigation": "önlem"}
  ],
  "deliverables": [
    {"type": "code|config|doc|design|test|other", "name": "isim", "description": "açıklama", "content": ""}
  ],
  "next_actions": ["adım1", "adım2"],
  "quality_notes": ["not1"]
}
"""

FALLBACK_FIELDS = {
    "decisions":    [],
    "assumptions":  [],
    "risks":        [],
    "deliverables": [],
    "next_actions": [],
    "quality_notes":[],
}


# ════════════════════════════════════════════════════════
# Parser — LLM yanıtını AgentOutput'a çevirir
# ════════════════════════════════════════════════════════
class AgentOutputParser:

    def parse(self, agent_id: str, raw: str) -> AgentOutput:
        """
        LLM yanıtını parse eder.
        JSON bozuksa graceful degradation — ham metni summary'e koyar.
        """
        errors: list[str] = []
        data   = self._extract_json(raw, errors)

        if data is None:
            # JSON çıkaramadık — ham metni özet olarak kullan
            return AgentOutput(
                agent_id=agent_id,
                summary=raw[:500].strip() or "(Yanıt alınamadı)",
                raw_response=raw,
                parse_errors=errors,
            )

        # Riskleri nesneye çevir
        risks = []
        for r in data.get("risks", []):
            if isinstance(r, dict):
                try:
                    sev = RiskSeverity(r.get("severity", "medium"))
                except ValueError:
                    sev = RiskSeverity.MEDIUM
                risks.append(Risk(
                    description=str(r.get("description", r.get("desc", ""))),
                    severity=sev,
                    mitigation=str(r.get("mitigation", "")),
                ))

        # Deliverable'ları nesneye çevir
        deliverables = []
        for d in data.get("deliverables", []):
            if isinstance(d, dict):
                deliverables.append(Deliverable(
                    type=str(d.get("type", "other")),
                    name=str(d.get("name", "")),
                    description=str(d.get("description", d.get("desc", ""))),
                    content=str(d.get("content", "")),
                ))

        summary = data.get("summary", "")
        if not summary and raw:
            summary = raw[:200]
            errors.append("summary alanı boş, ham yanıttan türetildi")

        return AgentOutput(
            agent_id=agent_id,
            summary=summary,
            decisions=list(data.get("decisions", [])),
            assumptions=list(data.get("assumptions", [])),
            risks=risks,
            deliverables=deliverables,
            next_actions=list(data.get("next_actions", [])),
            quality_notes=list(data.get("quality_notes", [])),
            raw_response=raw,
            parse_errors=errors,
        )

    def _extract_json(self, text: str, errors: list) -> dict | None:
        # Önce düz JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # ```json ... ``` bloğu
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                errors.append(f"JSON blok parse hatası: {e}")

        # Son çare: ilk { ... } bul
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e:
                errors.append(f"Fallback JSON parse hatası: {e}")

        errors.append("Geçerli JSON bulunamadı")
        return None


# Singleton
output_parser = AgentOutputParser()
