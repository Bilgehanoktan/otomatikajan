"""
Task Management Models and Services — Refactored from orchestrator.py
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class TaskStatus(str, Enum):
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
class SubTask:
    id:           str
    agent_id:     str
    prompt:       str
    status:       TaskStatus = TaskStatus.PENDING
    result:       str        = ""
    structured:   Any        = None   # AgentOutput nesnesi
    quality_score:float | None = None
    quality_detail: dict | None = None
    attempts:     int        = 0
    reviewed:     bool       = False
    review_notes: list       = field(default_factory=list)
    db_subtask_id: str | None = None
    created_at:   datetime   = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class ProjectTask:
    id:         str
    title:      str
    subtasks:   list[SubTask] = field(default_factory=list)
    status:     TaskStatus    = TaskStatus.PENDING
    created_at: datetime      = field(default_factory=lambda: datetime.now(timezone.utc))
    report:     str           = ""
    avg_quality:float | None  = None
    workflow_template: str    = "default"
    quality_profile: str      = "standard"
    acceptance_criteria: list[str] = field(default_factory=list)
    execution_context: dict   = field(default_factory=dict)

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

    def plan(self, title: str, description: str) -> list[SubTask]:
        # Lazy import to avoid circular dependencies
        try:
            from quality.output_schema import OUTPUT_FORMAT_INSTRUCTION
        except ImportError:
            OUTPUT_FORMAT_INSTRUCTION = ""
            
        subtasks = []
        for agent_id, contract in self.AGENT_CONTRACTS.items():
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
            subtasks.append(SubTask(
                id=str(uuid.uuid4())[:8],
                agent_id=agent_id,
                prompt=prompt,
            ))
        return subtasks

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

        lines = [f"# 📋 Proje Raporu: {task.title}", "",
                 f"**Durum:** {'✅ Tamamlandı' if not failed else '⚠️ Kısmi Başarı'}  |  ",
                 f"**Ajanlar:** {len(done)}/{len(task.subtasks)}  |  ",
                 f"**Ort. Kalite:** {avg_q:.0%}" if avg_q else "**Ort. Kalite:** —", ""]

        for st in task.subtasks:
            if st.status == TaskStatus.SKIPPED:
                lines.append(f"### ⏭️ {st.agent_id.upper()} (Atlandı - Bağımlılık Hatası)\n")
                continue
            icon = "✅" if st.status == TaskStatus.COMPLETED else "❌"
            q = f" | Q:{st.quality_score:.0%}" if st.quality_score is not None else ""
            rev = " 🔄" if st.reviewed else ""
            lines.append(f"### {icon} {st.agent_id.upper()}{q}{rev}")
            lines.append(st.structured.to_markdown() if hasattr(st.structured, 'to_markdown') else (st.result or "_Sonuç yok_"))
            lines.append("")

        task.avg_quality = avg_q
        return "\n".join(lines)
