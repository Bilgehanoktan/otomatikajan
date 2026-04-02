"""
Task Management Models and Services — Refactored from orchestrator.py
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class GovernanceStatus(str, Enum):
    PENDING          = "PENDING"
    QUEUED           = "QUEUED"
    RUNNING          = "RUNNING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    COMPLETED        = "COMPLETED"
    PARTIAL_COMPLETE = "PARTIAL_COMPLETE"
    ERROR            = "ERROR"
    CANCELLED        = "CANCELLED"
    PAUSED           = "PAUSED"
    RETRYING         = "RETRYING"
    SKIPPED          = "SKIPPED"

@dataclass
class GovernedTask:
    id:           str
    agent_id:     str
    prompt:       str
    status:       GovernanceStatus = GovernanceStatus.PENDING
    result:       str        = ""
    structured:   Any        = None   # AgentOutput nesnesi
    quality_score:float | None = None
    quality_detail: dict | None = None
    attempts:     int        = 0
    reviewed:     bool       = False
    review_notes: list       = field(default_factory=list)
    db_subtask_id: str | None = None
    created_at:   datetime   = field(default_factory=lambda: datetime.now(timezone.utc))
    # Faz 39: Risk ve Konsensüs
    risk_level:   str        = "low" # low, medium, high, critical
    consensus_required: bool = False
    consensus_score: float   = 0.0
    consensus_report: str | None = None
    # Faz 42: Bilişsel Devamlılık
    internal_monologue: str = ""
    # Faz 51: Rekürsif Dekompozisyon (Sovereign Depth)
    is_complex:   bool       = False
    parent_id:    str | None = None
    complexity_reasoning: str = ""

@dataclass
class SovereignGoal:
    id:         str
    title:      str
    description:str           = ""
    subtasks:   list[GovernedTask] = field(default_factory=list)
    status:     GovernanceStatus    = GovernanceStatus.PENDING
    created_at: datetime      = field(default_factory=lambda: datetime.now(timezone.utc))
    report:     str           = ""
    avg_quality:float | None  = None
    workflow_template: str    = "default"
    quality_profile: str      = "standard"
    acceptance_criteria: list[str] = field(default_factory=list)
    execution_context: dict   = field(default_factory=dict)
    
    def get_shared_state(self) -> dict:
        """Paylaşılan çalışma belleğini (Blackboard) döner."""
        return self.execution_context.get("shared_state", {})

    def update_shared_state(self, updates: dict):
        """Paylaşılan belleği günceller."""
        state = self.get_shared_state()
        state.update(updates)
        self.execution_context["shared_state"] = state

# Aliases for backward compatibility with older Cortex versions
ProjectTask = SovereignGoal
SubTask = GovernedTask
TaskStatus = GovernanceStatus

class TaskPlanner:
    # ── Gelişmiş Ajan Sözleşmeleri (Data Contracts & Scope Isolation) ──
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
        # Faz 37: Dinamik Sözleşme İyileştirmeleri (Meta-Learning)
        self.dynamic_contracts = {}
        # Faz 38: Sözleşme Geçmişi (Rollback Kapasitesi)
        self._contract_history = {} # agent_id -> list[dict]

    def update_contract(self, agent_id: str, new_contract: dict):
        """Otonom olarak iyileştirilen talimatları/sözleşmeleri kaydeder."""
        # Geçmişe kaydet
        if agent_id not in self._contract_history:
            self._contract_history[agent_id] = []
        
        # Mevcut olanı (varsa) geçmişe at
        if agent_id in self.dynamic_contracts:
            self._contract_history[agent_id].append(self.dynamic_contracts[agent_id])
            
        self.dynamic_contracts[agent_id] = new_contract

    def rollback_contract(self, agent_id: str):
        """Sözleşmeyi bir önceki sürüme geri döndürür."""
        if agent_id in self._contract_history and self._contract_history[agent_id]:
            last_good = self._contract_history[agent_id].pop()
            self.dynamic_contracts[agent_id] = last_good
            return True
        return False

    async def plan_sovereign(self, title: str, description: str, history: Optional[str] = None) -> list[SubTask]:
        """Faz 42 & 45: Bilişsel ketleme ve Tarihçe Damıtma destekli egemen planlama."""
        # Async retrieval of inhibitions
        inhibitions = []
        try:
            from core.agi.cognitive.synaptic_cortex import synaptic_cortex
            from db.session import get_db
            async with get_db() as db:
                inhibitions_data = await synaptic_cortex.get_architectural_inhibitions(db, limit=10)
                inhibitions = [i["body"] for i in inhibitions_data]
                
                # Faz 45: Bilişsel Devamlılık (Thought Monologue)
                monologue = await synaptic_cortex.get_continuous_monologue(db, limit=3)
        except Exception as e:
            from observability.logging import get_logger
            get_logger("agi_task_planner").warning(f"Failed to load cognitive background: {e}")
            monologue = ""

        # Faz 45: Tarihçe Damıtma (Distillation)
        distilled_history = ""
        if history and len(history) > 2000:
            distilled_history = await self.distill_execution_history(history)
        elif history:
            distilled_history = history

        # Lazy import to avoid circular dependencies
        try:
            from quality.output_schema import OUTPUT_FORMAT_INSTRUCTION
        except ImportError:
            OUTPUT_FORMAT_INSTRUCTION = ""
            
        subtasks = []
        for agent_id, base_contract in self.AGENT_CONTRACTS.items():
            contract = self.dynamic_contracts.get(agent_id, base_contract)
            
            inhibition_text = "\n".join([f"- {i}" for i in inhibitions]) if inhibitions else "- Yok."
            
            prompt = (
                f"Proje Görevi: {title}\n"
                f"Genel Açıklama: {description}\n\n"
                f"### BİLİŞSEL DEVAMLILIK (İÇSEL KONUŞMA)\n{monologue}\n\n"
                f"### STRATEJİK GEÇMİŞ (DAMITILMIŞ)\n{distilled_history if distilled_history else 'Yeni süreç.'}\n\n"
                f"### MİMARİ KISITLAMALAR (ÖNEMLİ)\n"
                f"Sistem öz-denetim geçmişine dayalı aşağıdaki yasaklara KESİNLİKLE uymalısın:\n"
                f"{inhibition_text}\n\n"
                f"Senin Uzmanlığın: {contract['skill']}\n"
                f"Kapsam Sınırın (BUNUN DIŞINA ÇIKMA): {contract['boundaries']}\n\n"
                f"Senden Beklenen Kesin Çıktı Formatı (Veri Sözleşmesi):\n{contract['expected_output']}\n\n"
                f"Talimat: Bu projeye SADECE kendi rolün ({agent_id}) çerçevesinde katkı sağla. "
                f"Eğer sana önceki ajanlardan bir 'Bağlam (Önceki Çıktılar)' verildiyse, onların mimari kararlarına saygı duy ve kendi çıktılarını onlara mükemmel bir şekilde entegre et.\n\n"
                f"{OUTPUT_FORMAT_INSTRUCTION}"
            )
            risk_info = self._assess_risk(agent_id, contract, title, description)
            
            subtasks.append(SubTask(
                id=str(uuid.uuid4())[:8],
                agent_id=agent_id,
                prompt=prompt,
                risk_level=risk_info["level"],
                consensus_required=risk_info["consensus_required"]
            ))
        return subtasks

    async def distill_execution_history(self, history: str) -> str:
        """Faz 45: Uzun yürütme geçmişini stratejik bir özet haline getirir."""
        from llm.model_orchestrator import ModelOrchestrator
        orch = ModelOrchestrator()
        
        prompt = f"""
        Aşağıdaki uzun yürütme geçmişini stratejik, teknik ve mimari bir özet haline getir.
        SADECE en kritik kararları, engelleri ve ulaşılan sonuçları tut. 
        Maksimum 500 kelime.
        
        GEÇMİŞ:
        {history}
        """
        try:
            resp = await orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Strateji Uzmanısın. Karmaşık verileri süzüp en değerli bilgiyi damıtırsın."
            )
            return resp.content
        except:
            return history[:1000] + "... [OTOMATİK KESİLDİ]"

    def plan(self, title: str, description: str) -> list[SubTask]:
        # Backward compatible sync version (No inhibitions)
        # Lazy import to avoid circular dependencies
        try:
            from quality.output_schema import OUTPUT_FORMAT_INSTRUCTION
        except ImportError:
            OUTPUT_FORMAT_INSTRUCTION = ""
            
        subtasks = []
        for agent_id, base_contract in self.AGENT_CONTRACTS.items():
            contract = self.dynamic_contracts.get(agent_id, base_contract)
            
            prompt = (
                f"Proje Görevi: {title}\n"
                f"Genel Açıklama: {description}\n\n"
                f"Senin Uzmanlığın: {contract['skill']}\n"
                f"Kapsam Sınırın (BUNUN DIŞINA ÇIKMA): {contract['boundaries']}\n\n"
                f"Senden Beklenen Kesin Çıktı Formatı (Veri Sözleşmesi):\n{contract['expected_output']}\n\n"
                f"Talimat: Bu projeye SADECE kendi rolün ({agent_id}) çerçevesinde katkı sağla. "
                f"Eğer sana önceki ajanlardan bir 'Bağlam (Önceki Çıktılar)' verildiyse, onların mimari kararlarına saygı duy ve kendi çıktılarını onlara mükemmel bir şekilde entegre et.\n\n"
                f"{OUTPUT_FORMAT_INSTRUCTION}"
            )
            risk_info = self._assess_risk(agent_id, contract, title, description)
            
            subtasks.append(SubTask(
                id=str(uuid.uuid4())[:8],
                agent_id=agent_id,
                prompt=prompt,
                risk_level=risk_info["level"],
                consensus_required=risk_info["consensus_required"]
            ))
        return subtasks

    def _assess_risk(self, agent_id: str, contract: dict, title: str, description: str) -> dict:
        """Faz 39: Görev için risk seviyesini ve konsensüs gerekliliğini belirler."""
        text = (title + " " + description + " " + contract.get("boundaries", "")).lower()
        
        # Kritik anahtar kelimeler
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
        elif len(description) > 500: # Karmaşık görevler
            risk_level = "medium"
            
        # Güvenlik ajanı her zaman yüksek riskli işlemler yapar
        if agent_id == "security" and risk_level != "critical":
            risk_level = "high"
            consensus_required = True
            
        return {"level": risk_level, "consensus_required": consensus_required}

class TaskStateService:
    def __init__(self):
        self._tasks: dict[str, ProjectTask] = {}
    def save(self, task: ProjectTask):
        self._tasks[task.id] = task
    def get(self, task_id: str) -> Optional[ProjectTask]:
        return self._tasks.get(task_id)
    def all_tasks(self) -> list[ProjectTask]:
        return list(self._tasks.values())

class ReportSynthesizer:
    def synthesize(self, task: ProjectTask) -> str:
        done    = [s for s in task.subtasks if s.status == TaskStatus.COMPLETED]
        failed  = [s for s in task.subtasks if s.status in [TaskStatus.ERROR, TaskStatus.SKIPPED]]
        scores  = [s.quality_score for s in done if s.quality_score is not None]
        avg_q   = sum(scores) / len(scores) if scores else None

        # --- AGI Cortex Analysis Header ---
        agi_meta = task.execution_context.get("agi_metadata", {})
        mood = task.execution_context.get("mood", "NEUTRAL")
        reasoning = task.execution_context.get("reflective_reasoning", "")
        
        lines = [f"# Proje Raporu: {task.title}", ""]
        
        if reasoning or agi_meta:
            lines.append("> [!NOTE]")
            lines.append("> **CORTEX ANALYSIS (v121.0)**")
            if reasoning:
                lines.append(f"> **Reasoning:** {reasoning}")
            if mood:
                lines.append(f"> **Affective State:** {mood}")
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
            if st.status == TaskStatus.SKIPPED:
                lines.append(f"### ⏭️ {st.agent_id.upper()} (Atlandı - Bağımlılık Hatası)\n")
                continue
            icon = "✅" if st.status == TaskStatus.COMPLETED else "❌"
            q = f" | Q:{st.quality_score:.0%}" if st.quality_score is not None else ""
            rev = " 🔄" if st.reviewed else ""
            lines.append(f"### {icon} {st.agent_id.upper()}{q}{rev}")
            
            # Subtask specific result
            res = st.structured.to_markdown() if hasattr(st.structured, 'to_markdown') else (st.result or "_Sonuç yok_")
            lines.append(res)
            lines.append("")

        task.avg_quality = avg_q
        return "\n".join(lines)
