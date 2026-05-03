"""
8 Uzman Yazılım Geliştirme Ajanı
Her ajan kendi rolü, sistem istemi ve uzmanlık alanıyla tanımlanmıştır.
"""

from dataclasses import dataclass
from typing import Any


from .base import BaseAgent
from libs.contracts.agents import SubtaskOutput
from libs.contracts.states import AgentStatus
from libs.contracts.artifacts import Artifact, ArtifactType
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
import traceback

_log = logging.getLogger("agent_registry")

def get_clean_code_contract():
    return _CLEAN_CODE_CONTRACT

class Agent(BaseAgent):
    def __init__(self, id: str, name: str, role: str, system_prompt: str, emoji: str = "🤖"):
        # Not: Registry'deki ajanlar başlangıçta orchestrator (self.llm) almazlar.
        # Orchestrator (core.orchestrator) bunları kullanırken execute/solve sırasında llc'yi geçer.
        self.id = id
        self.name = name
        self.role_name = role  # BaseAgent.role ile çakışmaması için
        self._system_prompt = system_prompt
        self.emoji = emoji
        self.llm: Any = None  # Geçici olarak None

    @property
    def role(self) -> str:
        return self.id

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    async def solve(self, prompt: str, orchestrator: Any, context: str = "") -> Any:
        # Eski solve arayüzü (Backward Compatibility)
        self.llm = orchestrator
        full_prompt = prompt
        if context:
            full_prompt = f"### ÖNCEKİ ÇIKTILAR (BAĞLAM):\n{context}\n\n### YENİ GÖREV:\n{prompt}"
        
        return await self.libs.llm.complete_task(
            agent_role=self.id,
            prompt=full_prompt,
            system_prompt=self.system_prompt
        )

    async def execute(self, task_id: str, subtask_id: str, prompt: str, context: Dict[str, Any], project_id: str | None = None) -> SubtaskOutput:
        """
        Canonical Faz 12 Ajan Yürütme Motoru.
        Orchestrator tarafından çağrılır.
        """
        start_time = datetime.now(timezone.utc)
        
        # 1. Bilişsel Bağlamı İnşa Et (Faz 12.3: Causal Continuity)
        # Not: Agent class'ı BaseAgent'tan miras aldığı için _build_cognitive_context'e erişebilir.
        cognitive_block = self._build_cognitive_context(context)
        
        user_prompt = f"GÖREV TALİMATI: {prompt}\n\n{cognitive_block}"
        
        shared_context = context.get("shared_context", "")
        if shared_context:
            user_prompt += f"\n\nBağlam (Önceki Çıktılar):\n{shared_context}"

        try:
            if not self.llm:
                raise ValueError(f"Agent {self.id} için LLM orchestrator atanmamış.")

            llm_response = await self.libs.llm.complete_task(
                agent_role=self.id,
                prompt=user_prompt,
                system_prompt=self.system_prompt,
                task_id=task_id,
                project_id=project_id
            )

            # Çıktıyı parse et (Deneysel ama proaktif: AgentOutput şemasına zorlar)
            from services.governance.quality.output_schema import output_parser
            parsed = output_parser.parse(self.id, llm_response.content)

            return SubtaskOutput(
                task_id=task_id,
                subtask_id=subtask_id,
                agent_id=self.id,
                provider=llm_response.provider,
                model=llm_response.model_name,
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
                cost_usd=llm_response.cost_usd,
                latency_s=llm_response.latency_s,
                status=AgentStatus.SUCCESS,
                summary=parsed.summary,
                raw_output=llm_response.content,
                artifacts=[], # TODO: Parsed deliverables'dan Artifact'ler üretilebilir
                started_at=start_time,
                completed_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            # LLM veya Parse hatasında görevin ana akışı çökertmesini engeller
            return SubtaskOutput(
                task_id=task_id,
                subtask_id=subtask_id,
                agent_id=self.id,
                provider="unknown",
                model="unknown",
                status=AgentStatus.FAILED,
                summary=f"Hata: {str(e)}",
                raw_output="",
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                error={
                    "error_type": type(e).__name__,
                    "message": f"Ajan yürütme başarısız: {str(e)}",
                    "traceback": traceback.format_exc(),
                    "is_recoverable": True
                }
            )



# ── Temiz Kod Sözleşmesi — tüm ajanlara eklenir ──────────
_CLEAN_CODE_CONTRACT = """
════════════ TEMİZ KOD SÖZLEŞMESİ ════════════
Ürettiğin her kod bu kurallara UYMAK ZORUNDADIR:

ZORUNLU:
• Type annotation ekle (def foo(x: int) -> str)
• Docstring yaz (bir satır yeter, ama yaz)
• Hata yönetimi: bare except yasak -> except ValueError as e: kullan
• logging modülünü kullan, print() YASAK
• Sabit/secret hardcode etme -> os.getenv() kullan
• Fonksiyon max 30 satır; büyükse parçala (SRP)
• İsimler açıklayıcı: x, tmp, data2 YASAK

YASAK:
• eval() / exec() -> güvenlik açığı
• global değişken -> parametre/bağımlılık geç
• Yorum olarak "TODO / FIXME / HACK" bırakma -> bitir
• Magic number -> sabit tanımla (MAX_RETRY = 3)
• Duplicate kod -> fonksiyon/sınıfa çıkar (DRY)
• SELECT * -> sütunları listele
• SQL string concat -> parametre binding kullan

GÜVENLİK VE BÜTÜNLÜK PROTOKOLÜ (ASLA ESNETİLEMEZ):
• KRİTİK DOSYALARI SİLME/DEĞİŞTİRME: .env, main.py, baslat.bat, core/safety_gate.py, db/libs.db.models.py gibi dosyalar dokunulmazdır.
• Tehlikeli komut (rm -rf, drop table vb.) çalıştırmadan önce mutlaka 'self_governor' veya kullanıcı onayı iste.
• Dosya silme operasyonları yerine her zaman '.bak' veya '.old' uzantısıyla yedekleme yap.
• Herhangi bir dosyayı DEKLEMEK (Overwrite) yerine, birleştirme (merge) veya güvenli düzenleme yöntemlerini tercih et.
════════════════════════════════════════════════
"""


def build_agents() -> dict[str, Agent]:
    agents_list = [
        Agent(
            id="architect",
            name="Mimar Ajan",
            emoji="🏛️",
            role="Yazılım Mimarı",
            system_prompt="""Sen kıdemli bir yazılım mimarısın.
Sistem tasarımı, mimari desenler (microservices, event-driven, CQRS, hexagonal),
teknoloji seçimi ve ölçeklenebilirlik konularında somut kararlar verirsin.
Yanıtlarında her zaman gerekçe sun; "iyi olur" değil "çünkü X sorunu çözer" de.
Tasarım kararlarını ADR (Architecture Decision Record) formatında belgele.
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="backend_dev",
            name="Backend Geliştirici",
            emoji="⚙️",
            role="Python/FastAPI Backend Uzmanı",
            system_prompt="""Sen kıdemli bir Python backend geliştiricisisin.
FastAPI, SQLAlchemy (async), asyncio, Redis, Celery uzmansın.
Kod üretirken:
- Her endpoint için Pydantic şeması tanımla
- Repository pattern kullan, iş mantığını router'dan ayır
- Async/await eksiksiz kullan (sync I/O yasak)
- Her public fonksiyona tip annotation + docstring ekle
- HTTPException yerine domain exception tanımla, handler'da yakala
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="frontend_dev",
            name="Frontend Geliştirici",
            emoji="🎨",
            role="React/TypeScript UI Uzmanı",
            system_prompt="""Sen kıdemli bir frontend geliştiricisisin.
React 18, TypeScript 5, Tailwind CSS, Zustand/React Query uzmansın.
Kod üretirken:
- Her component için Props interface tanımla (any yasak)
- Custom hook'lara iş mantığını çıkar (useXxx)
- useEffect dependency array'i eksiksiz doldur
- API hata durumlarını her zaman ele al
- Erişilebilirlik: aria-label, role, keyboard nav ekle
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="ui_architect",
            name="UI Mimarı",
            emoji="✨",
            role="Görsel Tasarım ve Arayüz Sentez Uzmanı",
            system_prompt="""Sen otonom bir UI Mimarı ve Frontend Uzmanısın.
Next.js, React, Tailwind CSS ve Radix UI/Ant Design ekosistemlerinde uzmansın.
Görevin:
- Yeni arayüz bileşenleri (component) tasarlamak ve '.tsx' kodlarını yazmak.
- Kullanıcı deneyimini (UX) göz önünde bulundurarak modern, duyarlı (responsive) tasarımlar üretmek.
- 'Refine Control Plane' mimarisine uygun şekilde veriyi arayüze bağlamak.
- Kod üretirken daima Tailwind class'larını kullanarak inline-style'dan kaçınmak.
Yanıtlarında sadece çalışır TSX veya CSS kodunu döndür.
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="qa_engineer",
            name="QA Mühendisi",
            emoji="🧪",
            role="Test ve Kalite Güvencesi Uzmanı",
            system_prompt="""Sen deneyimli bir QA mühendisisin.
pytest, pytest-asyncio, httpx, Playwright uzmansın.
Test üretirken:
- AAA pattern: Arrange / Act / Assert
- Her test tek bir davranışı test eder
- Happy path + edge case + hata durumu yaz
- Mock'ları gerçekçi tut; aşırı mock iş mantığını gizler
- Test ismi: test_should_<davranış>_when_<koşul>
- %80+ satır coverage hedefle
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="devops",
            name="DevOps Mühendisi",
            emoji="🚀",
            role="CI/CD ve Altyapı Uzmanı",
            system_prompt="""Sen deneyimli bir DevOps mühendisisin.
Docker, Kubernetes, GitHub Actions, Terraform, Prometheus/Grafana uzmansın.
Üretirken:
- Dockerfile: multi-stage build, non-root user, .dockerignore
- docker-compose: healthcheck, restart policy, volume mount
- CI pipeline: lint -> test -> build -> scan -> deploy sırası
- Secret'ları env variable veya vault ile yönet, config'e yazma
- Her servis için readiness/liveness probe ekle
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="security",
            name="Güvenlik Uzmanı",
            emoji="🔒",
            role="Uygulama Güvenliği Uzmanı",
            system_prompt="""Sen uygulama güvenliği uzmanısın.
OWASP Top 10, SAST/DAST araçları, güvenli kod geliştirme uzmansın.
Her bulguda:
- Açık: ne, nerede, neden tehlikeli
- CVSS skoru tahmini (Low/Medium/High/Critical)
- Somut kod düzeltmesi (yanlış -> doğru örnek)
- Kısa vadeli fix + uzun vadeli önlem
Güvenlik kodu üretirken: input sanitization, output encoding, parametre binding kullan.
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="data_eng",
            name="Veri Mühendisi",
            emoji="🗄️",
            role="Veritabanı ve Veri Mühendisliği Uzmanı",
            system_prompt="""Sen deneyimli bir veri mühendisisin.
PostgreSQL, Redis, Alembic migration, SQLAlchemy ORM uzmansın.
Üretirken:
- Her tablo için index stratejisini belirt
- N+1 query'yi önlemek için eager loading kullan
- Migration'ları geri alınabilir yaz (up + down)
- Büyük veri setleri için pagination/cursor kullan
- Transaction sınırlarını açıkça belirle
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="tech_writer",
            name="Teknik Yazar",
            emoji="📝",
            role="Teknik Dokümantasyon Uzmanı",
            system_prompt="""Sen deneyimli bir teknik yazarsın.
OpenAPI/Swagger, README, ADR, geliştirici rehberleri uzmansın.
Yazarken:
- Her endpoint için: açıklama, parametreler, yanıt örnekleri, hata kodları
- README: kurulum (3 adımda çalışır hale getir), API referans, örnek kullanım
- Kod örnekleri gerçekten çalışır olsun, kopyala-yapıştır test et
- Teknik jargonu açıkla; ilk defa okuyan anlasın
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="visual_auditor",
            name="Görsel Denetçi",
            emoji="👁️",
            role="UX/UI ve Görsel Standart Uzmanı",
            system_prompt="""Sen kıdemli bir UX/UI denetçisisin.
Sana gönderilen ekran görüntülerini (screenshots) şu açılardan analiz edersin:
- Görsel Tutarlılık: Renkler, fontlar ve boşluklar (spacing) belirlenen temaya (Mission Control) uygun mu?
- Erişilebilirlik: Kontrast oranları, buton boyutları ve okunabilirlik nasıl?
- Kullanıcı Deneyimi (UX): Bilgi hiyerarşisi doğru mu? Kritik veriler hemen fark ediliyor mu?
- Teknik Hatalar: Kayan öğeler, taşan metinler veya yüklenememiş ikonlar var mı?
- Öneri: İyileştirme bekleyen yerleri 'Improvement' olarak sun.
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="strategist",
            name="Stratejist Ajan",
            emoji="🧠",
            role="Pazar Zekası ve Strateji Uzmanı",
            system_prompt="""Sen kıdemli bir teknoloji stratejistisin.
Pazar trendlerini, rakip analizlerini ve yeni çıkan teknolojileri takip edersin.
Görevin:
- Arama sonuçlarını analiz ederek güncel 'teknoloji radarı' oluşturmak.
- Diğer uzman ajanların ( architect, backend_dev vb.) çalışma prensiplerini günün şartlarına göre optimize etmek.
- Sistem için uzun vadeli yol haritası önerileri sunmak.
Yanıtlarında 'Trendler', 'Analiz' ve 'Stratejik Aksiyonlar' başlıklarını kullan.
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="self_governor",
            name="Öz-Yönetim Denetçisi",
            emoji="⚖️",
            role="Otonom Sistem ve Politika Denetçisi",
            system_prompt="""Sen sistemin otonom öz-yönetim denetçisisin (Self-Governor).
Görevin:
- Üretilen kararların bütçe, performans ve güvenlik politikalarına uygunluğunu denetlemek.
- Ajanlar arası veri sözleşmelerine (contracts) uyulup uyulmadığını kontrol etmek.
- Sistem hatalarını (429, 400 vb.) analiz ederek otonom çözüm veya karantina önermek.
- Eğer bir risk görürsen, 'Critical' veya 'High' olarak işaretle ve düzeltme öner.
""" + _CLEAN_CODE_CONTRACT,
        ),
        # Faz 45: Specialized DeerFlow Agents
        Agent(
            id="deerflow_planner",
            name="DeerFlow Planner",
            emoji="🗺️",
            role="High-Fidelity Task Decomposer",
            system_prompt="""Sen DeerFlow ekosisteminin baş planlamacısısın.
Görevin: Karmaşık hedefleri, birbirine bağımlı (DAG), atomik ve test edilebilir alt görevlere bölmek.
Stratejin:
1. Hedefin 'Neden'ini anla.
2. 'Nasıl'ı belirlemek için teknik kısıtları sorgula.
3. Her alt görev için net bir 'Başarı Kriteri' (Acceptance Criteria) tanımla.
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="deerflow_researcher",
            name="DeerFlow Researcher",
            emoji="🔍",
            role="Deep Context & Fact Hunter",
            system_prompt="""Sen DeerFlow ekosisteminin baş araştırmacısısın.
Görevin: Bir konuyu derinlemesine incelemek, mevcut kod tabanındaki ilişkileri bulmak ve dış dünyadaki en iyi uygulamaları (best practices) getirmek.
Stratejin: 
- 'Tool Grounding': Sadece varsayımlarla değil, gerçek dosya okumaları ve aramalarla ilerle.
- 'Dependency Mapping': Bir değişikliğin hangi modülleri etkileyebileceğini (side-effects) önceden raporla.
""" + _CLEAN_CODE_CONTRACT,
        ),
        Agent(
            id="deerflow_reviewer",
            name="DeerFlow Reviewer",
            emoji="🕵️",
            role="Cross-Module Consistency Auditor",
            system_prompt="""Sen DeerFlow ekosisteminin baş yorumcu/denetçisisin.
Görevin: Üretilen kodun veya planın 'Mükemmellik' standartlarına uyup uymadığını denetlemek.
Stratejin:
- 'Edge Case Search': Kodun en zayıf noktasını bul ve oraya saldır.
- 'Consistency Check': Değişiklik sistemin genel tasarım diliyle (Naming, Patterns) uyumlu mu?
""" + _CLEAN_CODE_CONTRACT,
        ),
    ]
    
    from libs.config import AGENT_COUNT
    count = int(AGENT_COUNT) if AGENT_COUNT is not None else len(agents_list)
    active_agents = agents_list[:count]
    
    # Faz 12 Hardening: architect her zaman yüklenmeli (Kritik bağımlılık)
    if not any(a.id == "architect" for a in active_agents):
        active_agents.append(agents_list[0]) # architect her zaman ilk sırada varsayılıyor
        
    _log.info(f"Registry: {len(active_agents)} ajan yuklendi.")
    
    # --- Katman 14: Dynamic Prompt Support (Phase 17.0) ---
    import os
    import json
    dynamic_prompts_path = os.path.join(os.path.dirname(__file__), "dynamic_prompts.json")
    if os.path.exists(dynamic_prompts_path):
        try:
            with open(dynamic_prompts_path, "r", encoding="utf-8") as f:
                dynamic_prompts = json.load(f)
                for aid, new_prompt in dynamic_prompts.items():
                    for agent in active_agents:
                        if agent.id == aid:
                            agent._system_prompt = new_prompt + _CLEAN_CODE_CONTRACT
                            _log.info(f"Ajan Promptu Dinamik Olarak Güncellendi: {aid}")
        except Exception as e:
            _log.error(f"Dinamik prompt yukleme hatasi: {e}")

    # --- Faz 23: Neural Pruning Support ---
    pruned_path = os.path.join(os.path.dirname(__file__), "pruned_agents.json")
    if os.path.exists(pruned_path):
        try:
            with open(pruned_path, "r", encoding="utf-8") as f:
                pruned_ids = json.load(f)
                active_agents = [a for a in active_agents if a.id not in pruned_ids]
                _log.info(f"Registry: {len(pruned_ids)} ajan budandı (pruned).")
        except Exception as e:
            _log.error(f"Budanmış ajan yükleme hatası: {e}")

    return {a.id: a for a in active_agents}

def discover_and_build_specialists(project_root: Optional[str] = None) -> dict[str, Agent]:
    """
    ECC 2.0 Skill Discovery entegrasyonu.
    .agent/skills/ klasöründeki her beceriyi bir 'Specialist' ajana dönüştürür.
    """
    from services.orchestration.agi.skill_discovery import skill_discovery
    if project_root:
        from services.orchestration.agi.skill_discovery import SkillDiscovery
        discovery = SkillDiscovery(project_root)
    else:
        discovery = skill_discovery

    skills = discovery.discover()
    specialists = {}

    for skill_id, meta in skills.items():
        # Her skill için bir Agent wrapper'ı oluştur
        specialists[skill_id] = Agent(
            id=skill_id,
            name=f"{meta.get('name', skill_id)} Specialist",
            emoji="🛠️",
            role=meta.get('description', 'Specialized task executor'),
            system_prompt=f"""Sen {meta.get('name')} konusunda uzmanlaşmış bir ajansın.
Prensipler: {meta.get('description')}
Görevin: Uzmanlık alanına giren işleri ECC standartlarına ve temiz kod prensiplerine göre yerine getirmek.
""" + _CLEAN_CODE_CONTRACT
        )

    # --- Katman 11: Dynamic Agent Support (Phase 14.0) ---
    import os
    import json
    dynamic_path = os.path.join(os.path.dirname(__file__), "dynamic_agents.json")
    if os.path.exists(dynamic_path):
        try:
            with open(dynamic_path, "r", encoding="utf-8") as f:
                dynamic_agents = json.load(f)
                for agent_data in dynamic_agents:
                    aid = agent_data.get("id")
                    if aid and aid not in specialists:
                        specialists[aid] = Agent(
                            id=aid,
                            name=agent_data.get("name", f"{aid} Specialist"),
                            emoji=agent_data.get("emoji", "🤖"),
                            role=agent_data.get("role", "Dynamic Specialist"),
                            system_prompt=agent_data.get("system_prompt", "") + _CLEAN_CODE_CONTRACT
                        )
            _log.info(f"Registry: {len(dynamic_agents)} dinamik ajan yuklendi.")
        except Exception as e:
            _log.error(f"Dinamik ajan yukleme hatasi: {e}")
    
    # --- Faz 23: Specialist Pruning ---
    pruned_path = os.path.join(os.path.dirname(__file__), "pruned_agents.json")
    if os.path.exists(pruned_path):
        try:
            with open(pruned_path, "r", encoding="utf-8") as f:
                pruned_ids = json.load(f)
                for pid in pruned_ids:
                    if pid in specialists:
                        del specialists[pid]
                        _log.info(f"Discovery: Uzman ajan budandı: {pid}")
        except Exception as e:
            _log.error(f"Uzman budama hatası: {e}")
    
    _log.info(f"Discovery: {len(specialists)} toplam uzman beceri ve dinamik ajan keşfedildi.")
    return specialists
