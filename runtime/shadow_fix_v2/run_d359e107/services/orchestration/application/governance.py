import uuid
import asyncio
from typing import Any, Optional, List, Dict
from datetime import datetime, timezone
from services.observability.logging import get_logger
from services.orchestration.domain.models import (
    GovernedTask, SovereignGoal, GovernanceStatus
)

_log = get_logger("agi_governance")

class TaskPlanner:
    """
    Görev Planlama Servisi (Application Layer).
    [Faz 12.1] Hedefleri alt görevlere (subtasks) böler ve ajan sözleşmelerini yönetir.
    """
    AGENT_CONTRACTS = {
        "architect": {
            "skill": "Sistem tasarımı, mimari kararlar, teknoloji seçimi",
            "boundaries": "Kod yazma, sadece mimari iskeleti, bileşenleri ve API sınırlarını belirle.",
            "expected_output": "1. ADR (Mimari Karar Kaydı)\n2. Modül hiyerarşisi\n3. Kullanılacak teknolojiler ve gerekçeleri"
        },
        "backend_dev": {
            "skill": "Python/FastAPI/Go backend kodlama",
            "boundaries": "Arayüz (UI) veya DevOps konularına girme. Sadece Mimarın belirlediği sınırlarda backend API tasarla.",
            "expected_output": "1. Pydantic şemaları\n2. API endpoint (Router) yapıları\n3. İş mantığı (Service) akışları"
        },
        "frontend_dev": {
            "skill": "React/TypeScript UI geliştirme",
            "boundaries": "Backend API'sini değiştirmeye çalışma. Mevcut / tasarlanan API'yi tüketecek şekilde ekran tasarla.",
            "expected_output": "1. Component ağacı hiyerarşisi\n2. State yönetimi (Zustand/Context)\n3. API çağrı kurguları"
        },
        "qa_engineer": {
            "skill": "Test yazımı, hata tespiti, kalite güvencesi",
            "boundaries": "Yeni özellik (feature) kodu yazma, sadece diğerlerinin yazdığı / tasarladığı yapıyı test et.",
            "expected_output": "1. Happy-path ve Edge-case test senaryoları\n2. Örnek Pytest / Playwright iddiaları (assertions)"
        },
        "devops": {
            "skill": "CI/CD, Docker, Kubernetes, deployment",
            "boundaries": "Uygulama kaynak kodunu değiştirme. Sadece altyapıyı ve dağıtım boru hattını (pipeline) kurgula.",
            "expected_output": "1. Dockerfile optimizasyonları\n2. docker-compose servis ağı\n3. CI/CD pipeline adımları"
        },
        "security": {
            "skill": "Güvenlik taraması, zafiyet analizi, OWASP",
            "boundaries": "Sistemi baştan tasarlama, sadece mevcut tasarımdaki olası açıkları bul ve yamala.",
            "expected_output": "1. Tehdit Modeli (Threat Model)\n2. Giriş/Çıkış doğrulama (Input Validation) kuralları"
        },
        "data_eng": {
            "skill": "Veritabanı tasarımı, SQL/NoSQL, migration",
            "boundaries": "Web API yazma, sadece veri saklama, ilişkiler ve optimizasyona odaklan.",
            "expected_output": "1. Veritabanı şema tasarımı (ERD özeti)\n2. Indexleme stratejisi\n3. Alembic migration planı"
        },
        "tech_writer": {
            "skill": "Dokümantasyon, API dokümanı, README",
            "boundaries": "Sistem mimarisini veya kodu eleştirme, sadece olanı son kullanıcı ve geliştiriciler için belgele.",
            "expected_output": "1. Kurulum talimatları\n2. API kullanım örnekleri\n3. Genel geliştirici rehberi"
        },
        "self_governor": {
            "skill": "Sistem sağlığı, otonom politika yönetimi ve hata analizi",
            "boundaries": "Teknik geliştirme yapma. Sadece diğer ajanların çıktılarını sistem bütünlüğü, maliyet ve politika uyumu açısından denetle.",
            "expected_output": "1. Öz-Yönetim Raporu\n2. Kök Neden Analizi (Hata varsa)\n3. Politika Önerileri (preferred_provider vb.)"
        },
    }

    def __init__(self):
        self.dynamic_contracts = {}
        self._contract_history = {} 

    def plan(self, title: str, description: str) -> List[GovernedTask]:
        # Sync planner bridge for test compatibility (Phase 37)
        agent_id = "architect"
        base_contract = self.AGENT_CONTRACTS.get(agent_id)
        contract = self.dynamic_contracts.get(agent_id, base_contract)
        
        prompt = (
            f"STRATEJİK ALT-GÖREV: Architect Task\n"
            f"Senin Uzmanlığın: {contract['skill']}\n"
            f"Beklenen Çıktı: {contract['expected_output']}\n"
        )
        
        gt = GovernedTask(
            id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            prompt=prompt,
            risk_level="low"
        )
        return [gt]

    async def plan_sovereign(self, title: str, description: str, history: Optional[str] = None) -> List[GovernedTask]:
        """Faz 51 [Sovereign Evolution]: Rekürsif Stratejik Dekompozisyon destekli planlama."""
        from services.orchestration.agi.cognitive.recursive_decomposer import RecursiveDecomposer
        decomposer = RecursiveDecomposer()
        
        inhibitions = []
        monologue = ""
        try:
            from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
            from libs.db.session import session_scope
            async with session_scope() as db:
                inhibitions_data = await synaptic_cortex.get_architectural_inhibitions(db, limit=10)
                inhibitions = [i["body"] for i in inhibitions_data]
                monologue = await synaptic_cortex.get_continuous_monologue(db, limit=3)
        except Exception as e:
            _log.warning(f"Failed to load cognitive background: {e}")

        context = {
            "monologue": monologue,
            "inhibitions": inhibitions,
            "history_summary": history[:500] if history else ""
        }
        strategic_tasks = await decomposer.decompose_goal(title, description, context)
        
        subtasks = []
        task_mapping = {} 
        
        for st in strategic_tasks:
            agent_id = st.get("agent_id", "architect")
            base_contract = self.AGENT_CONTRACTS.get(agent_id, self.AGENT_CONTRACTS["architect"])
            contract = self.dynamic_contracts.get(agent_id, base_contract)
            
            internal_id = str(uuid.uuid4())[:8]
            task_mapping[st.get("task_id", "unknown")] = internal_id
            
            inhibition_text = f"MİMARİ KISIT: {st.get('inhibition', 'Yok.')}\n" + \
                               "\n".join([f"- {i}" for i in inhibitions]) if inhibitions else "- Yok."
            
            prompt = (
                f"STRATEJİK ALT-GÖREV: {st.get('objective', title)}\n"
                f"Üst-Hedef: {title}\n"
                f"### BİLİŞSEL DEVAMLILIK\n{monologue}\n\n"
                f"### ÖZEL İNHİBİSYONLAR (YASAKLAR)\n{inhibition_text}\n\n"
                f"### KABUL KRİTERLERİ\n" + "\n".join([f"- {c}" for c in st.get('acceptance_criteria', [])]) + "\n\n"
                f"Senin Uzmanlığın: {contract['skill']}\n"
                f"Beklenen Çıktı: {contract['expected_output']}\n"
            )
            
            risk_info = self._assess_risk(agent_id, contract, title, st.get('objective', ''))
            internal_deps = [task_mapping[d] for d in st.get("dependencies", []) if d in task_mapping]
            
            gt = GovernedTask(
                id=internal_id,
                agent_id=agent_id,
                prompt=prompt,
                risk_level=risk_info["level"],
                consensus_required=risk_info["consensus_required"],
                is_complex=True,
                complexity_reasoning=st.get("objective", ""),
                dependencies=internal_deps
            )
            subtasks.append(gt)
            
        return subtasks

    def _assess_risk(self, agent_id: str, contract: dict, title: str, description: str) -> dict:
        text = (title + " " + description + " " + contract.get("boundaries", "")).lower()
        critical_keywords = ["delete", "root", "rm -rf", "wipe", "format", "production", "security bypass", "override safety"]
        high_risk_keywords = ["modify core", "refactor api", "database migration", "auth change", "credentials"]
        
        risk_level = "low"
        consensus_required = False
        
        if any(k in text for k in critical_keywords):
            risk_level = "critical"
            consensus_required = True
        elif any(k in text for k in high_risk_keywords):
            risk_level = "high"
            consensus_required = True
        elif len(description) > 500:
            risk_level = "medium"
            
        if agent_id == "security" and risk_level != "critical":
            risk_level = "high"
            consensus_required = True
            
        return {"level": risk_level, "consensus_required": consensus_required}

import json

class TaskStateService:
    def __init__(self):
        self._tasks: Dict[str, SovereignGoal] = {}
    def save(self, task: SovereignGoal):
        self._tasks[task.id] = task
    def get(self, task_id: str) -> Optional[SovereignGoal]:
        return self._tasks.get(task_id)
    def all_tasks(self) -> List[SovereignGoal]:
        return list(self._tasks.values())

class ReportSynthesizer:
    async def synthesize_structured(self, task: SovereignGoal, cortex=None) -> dict:
        """
        [Faz 13.04.2] Generates a structured JSON report following the mandated schema.
        Uses LLM synthesis for concrete findings if cortex is available.
        """
        def is_completed(s):
            status_str = str(s.status).upper()
            return "COMPLETED" in status_str or "DONE" in status_str or status_str == "SUCCESS"

        def is_failed(s):
            status_str = str(s.status).upper()
            return "ERROR" in status_str or "FAILED" in status_str or "CRITICAL" in status_str

        done    = [s for s in task.subtasks if is_completed(s)]
        failed  = [s for s in task.subtasks if is_failed(s)]
        scores  = [getattr(s, "quality_score", None) for s in done if getattr(s, "quality_score", None) is not None]
        avg_q   = sum(scores) / len(scores) if scores else 0.0
        
        # 1. Extract Findings (LLM or Heuristic)
        findings = []
        if cortex and done:
            findings = await self._extract_findings_llm(done, cortex)
        
        # Fallback if LLM extraction failed or returned too few
        if len(findings) < 3:
            for s in done:
                if len(findings) >= 3: break
                findings.append({
                    "severity": "MEDIUM" if s.quality_score > 0.6 else "HIGH",
                    "category": "OPERATIONAL",
                    "title": f"Ajan {s.agent_id} Görev İcrası",
                    "evidence": str(s.result)[:300] if s.result else "Kanıt bulunamadı.",
                    "impact": "Sistem durumunda değişiklik saptandı.",
                    "recommendation": "Ajan çıktısı manuel olarak doğrulanmalı."
                })

        # 2. Extract Risks & Recommendations
        risks = []
        for s in failed:
            risks.append(f"Ajan {s.agent_id} adımı başarısız oldu (Hata: {s.result or 'Unknown'})")
        if avg_q < 0.6:
            risks.append("Genel kalite skoru kritik seviyenin altında.")

        recs = ["Tüm bulgular için teknik doğrulama (QA) yapılmalı."]
        if risks:
            recs.append("Başarısız olan adımlar için manuel telafi süreci başlatılmalı.")

        # 3. Assemble JSON Report
        report_data = {
            "title": task.title or "Sistem Analizi",
            "executive_summary": task.execution_context.get("reflective_reasoning") or f"Görev {len(done)} ajan tarafından başarıyla icra edildi. Ortalama kalite: {avg_q:.2f}",
            "scope": task.execution_context.get("scope", "Full System"),
            "analysis_type": "RESEARCH",
            "agent_count": len(done),
            "average_quality": round(avg_q, 2),
            "findings": findings[:5], # Keep max 5 for UI stability
            "risks": risks,
            "recommendations": recs,
            "next_actions": [
                "Hafıza katmanının güncellenmesi",
                "Operatör onayı ve yama (patch) hazırlığı"
            ],
            "limitations": [
                "Analiz sadece aktif workspace dosyaları ile sınırlıdır.",
                "Zaman kısıtı nedeniyle derinlemesine stres testi yapılmamıştır."
            ]
        }

        # Side effect: Governance Advisory
        if avg_q < 0.5 or failed:
            from services.orchestration.domain.events import event_bus
            asyncio.create_task(event_bus.emit(
                "GOVERNANCE_ADVISORY",
                severity="error" if failed else "warning",
                message=f"Workflow {task.id} low quality or partial failure.",
                payload={"project_id": task.id, "avg_quality": avg_q, "failed_count": len(failed)}
            ))

        return report_data

    async def _extract_findings_llm(self, subtasks: list, cortex) -> list:
        """Uses LLM to synthesize concrete, structured findings from agent outputs."""
        outputs = "\n\n".join([f"AGENT: {s.agent_id}\nRESULT: {s.result}" for s in subtasks if s.result])
        if not outputs: return []

        prompt = f"""
As a Senior Research Synthesizer, analyze the following agent outputs and extract exactly 3 concrete, high-quality findings.
Each finding must be significant and structured as JSON.

AGENT OUTPUTS:
{outputs}

Return ONLY a JSON array with exactly this structure:
[
  {{
    "severity": "HIGH/MEDIUM/LOW",
    "category": "API/Performance/Security/Reliability/Logic",
    "title": "Short descriptive title",
    "evidence": "Concrete proof or snippet from the agent output",
    "impact": "Technical or business impact",
    "recommendation": "Actionable fix or improvement"
  }}
]
"""
        try:
            res = await cortex.model_orch.generate(prompt, system_prompt="You are a precise JSON synthesis engine.")
            # JSON cleaning
            clean_res = res.strip()
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[1].split("```")[0].strip()
            
            data = json.loads(clean_res)
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            _log.warning(f"LLM Finding extraction failed: {e}")
            return []

    def synthesize_markdown(self, report_data: dict) -> str:
        """Converts structured JSON report back to beautiful Markdown for legacy UI support."""
        lines = [f"# {report_data['title']}", ""]
        
        lines.append("## 📝 Yönetici Özeti")
        lines.append(report_data['executive_summary'])
        lines.append("")
        
        lines.append("## 🔍 Kapsam ve Metrikler")
        lines.extend([
            f"- **Kapsam:** {report_data['scope']}",
            f"- **Analiz Tipi:** {report_data['analysis_type']}",
            f"- **Aktif Ajanlar:** {report_data['agent_count']}",
            f"- **Ortalama Kalite:** {report_data['average_quality']:.0%}",
            ""
        ])

        lines.append("## 🤖 Somut Bulgular (Findings)")
        for f in report_data['findings']:
            severity_icon = "🔴" if f['severity'] == "HIGH" else "🟡" if f['severity'] == "MEDIUM" else "🟢"
            lines.append(f"### {severity_icon} {f['title']} ({f['category']})")
            lines.append(f"**Kanıt:** {f['evidence']}")
            lines.append(f"**Etki:** {f['impact']}")
            lines.append(f"**Öneri:** {f['recommendation']}")
            lines.append("")

        if report_data['risks']:
            lines.append("## ⚠️ Tespit Edilen Riskler")
            for r in report_data['risks']:
                lines.append(f"- {r}")
            lines.append("")

        lines.append("## 🚀 Sonraki Adımlar")
        for a in report_data['next_actions']:
            lines.append(f"- [ ] {a}")
        lines.append("")
        
        return "\n".join(lines)

    async def synthesize(self, task: SovereignGoal, cortex=None) -> str:
        """Legacy wrapper that returns Markdown string."""
        data = await self.synthesize_structured(task, cortex)
        return self.synthesize_markdown(data)

