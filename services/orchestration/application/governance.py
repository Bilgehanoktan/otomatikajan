import uuid
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
    def synthesize(self, task: SovereignGoal) -> str:
        done    = [s for s in task.subtasks if s.status == GovernanceStatus.COMPLETED]
        failed  = [s for s in task.subtasks if s.status in [GovernanceStatus.ERROR, GovernanceStatus.SKIPPED]]
        scores  = [s.quality_score for s in done if s.quality_score is not None]
        avg_q   = sum(scores) / len(scores) if scores else None
        
        agi_meta = task.execution_context.get("agi_metadata", {})
        mood = task.execution_context.get("mood", "NEUTRAL")
        reasoning = task.execution_context.get("reflective_reasoning", "")
        
        lines = [f"# Proje Raporu: {task.title}", ""]
        if reasoning or agi_meta:
            lines.append("> [!NOTE]")
            lines.append("> **CORTEX ANALYSIS (v121.0)**")
            if reasoning: lines.append(f"> **Reasoning:** {reasoning}")
            if mood: lines.append(f"> **Affective State:** {mood}")
            if agi_meta.get("verification"):
                score = agi_meta["verification"].get("integration_reality_score", 0) * 100
                lines.append(f"> **Reality Score:** {score:.0f}%")
            lines.append("")

        lines.extend([
            f"**Durum:** {'Tamamlandı' if not failed else 'Kısmi Başarı'}  |  ",
            f"**Ajanlar:** {len(done)}/{len(task.subtasks)}  |  ",
            f"**Ort. Kalite:** {avg_q:.0%}" if avg_q else "**Ort. Kalite:** ---", ""
        ])

        for st in task.subtasks:
            if st.status == GovernanceStatus.SKIPPED:
                lines.append(f"### ⏭️ {st.agent_id.upper()} (Atlandı - Bağımlılık Hatası)\n")
                continue
            icon = "✅" if st.status == GovernanceStatus.COMPLETED else "❌"
            q = f" | Q:{st.quality_score:.0%}" if st.quality_score is not None else ""
            rev = " 🔄" if st.reviewed else ""
            lines.append(f"### {icon} {st.agent_id.upper()}{q}{rev}")
            lines.append(st.result or "_Sonuç yok_")
            lines.append("")

        task.avg_quality = avg_q
        return "\n".join(lines)
