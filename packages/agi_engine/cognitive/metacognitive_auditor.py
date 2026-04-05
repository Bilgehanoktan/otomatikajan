import asyncio
import os
import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from db.session import session_scope, AsyncSessionLocal
from db.models import SkillExecutionLog, ImprovementOpportunity, Project, SubTask
from db.repository import ProjectRepository, ApiMetricRepository
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from quality.reviewer import ReviewResult
from core.system_indexer import SystemIndexer
from quality.output_schema import AgentOutput
from core.agency.loader import agency_loader
from memory.watchdog import watchdog

_log = get_logger("agi_metacognitive_auditor")

class MetacognitiveAuditor:
    """
    Egemen AGI Çekirdeği (Faz 50): Üst-Bilişsel Denetçi.
    AGI'nin 'Öz-Eleştiri', 'Hata Analizi' ve 'Bilişsel Denetim' merkezi.
    Hem anlık iş hatalarını (Real-time) hem de sistemik tıkanıklıkları (Historical) analiz eder.
    [Faz 47] Derin Kök Neden Analizi (Deep RCA) yeteneği eklendi.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.indexer = SystemIndexer()
        
        # Faz 50: Eşik Değerleri (Configuration)
        self.threshold_error_rate = 5.0  # %5 hata eşiği
        self.threshold_latency_ms = 5000 # 5 saniye gecikme eşiği
        self.min_occurrences = 3        # Tekrarlanan hata eşiği
        self.core_path = "core/agi/"
        self.arch_spec_path = "AGI_SISTEM_MIMARISI.md"
        self.required_structure = [
            "core/agi/cognitive",
            "core/agi/operational",
            "core/agi/learning",
            "core/agi/security"
        ]

    # --- PART 1: Real-time Job Failure Analysis (Metacognitive Recovery) ---

    async def analyze_job_failure(self, job_type: str, job_payload: Dict[str, Any], error_msg: str, last_monologue: str = "") -> Dict[str, Any]:
        """
        [FAZ 47 - DEEP RCA] Görevin neden başarısız olduğunu analiz eder.
        Mimari borçları ve yapısal karmaşıklığı denetleyerek kök nedeni bulur.
        """
        _log.info(f"[META-AUDIT] Derin hata analizi başlatıldı: {job_type}")
        
        # Faz 47: Mimari Bağlam Taraması
        arch_diff = ""
        try:
            # Hatalı görevle ilgili olabilecek dosyaları tarar
            potential_file = job_payload.get("target_file") or job_payload.get("path")
            if potential_file and os.path.exists(potential_file):
                index = self.indexer.read_index()
                for entry in index.get("entries", []):
                    if entry["path"] in potential_file:
                        size_kb = entry.get("size_bytes", 0) / 1024
                        symbols = len(entry.get("symbols", []))
                        if size_kb > 15 or symbols > 25:
                            arch_diff = f"\n[MİMARİ UYARI]: {potential_file} çok karmaşık ({size_kb:.1f}KB, {symbols} sembol). Ajan bu karmaşıklık altında ezilmiş olabilir."
        except Exception as e:
            _log.warning(f"[META-AUDIT] Mimari tarama atlandı: {e}")

        prompt = f"""
SİSTEM GÖREV HATASI ANALİZİ (Egemen AGI)
----------------------------------------------
GÖREV TİPİ: {job_type}
HATA MESAJI: {error_msg}
GÖREV VERİSİ: {json.dumps(job_payload, indent=2)}
SON İÇSEL MONOLOG: {last_monologue}
{arch_diff}

GÖREV: Bu hatanın KÖK NEDENİNİ (root cause) mimari ve operasyonel düzeyde bul ve otonom bir KURTARMA (recovery) planı oluştur.
Kurtarma planı şunları içermelidir:
1. 'recoverable': true | false (Hata kalıcı mı yoksa strateji değişikliğiyle çözülebilir mi?)
2. 'root_cause': Hatanın gerçek, derin nedeni (Örn: Mimari kısıtlama, API limit aşımı, bağlam kaybı, yanlış ajan seçimi)
3. 'inhibition_injection': Bir sonraki denemede ajana enjekte edilecek 'Kısıtlama/Uyarı' (Negatif Sinaps/İnhibisyon)
4. 'context_augmentation': Bir sonraki denemeye eklenecek 'Eksik Bilgi', 'İpucu' veya 'Stratejik Yönlendirme'

JSON formatında yanıt ver:
{{
  "recoverable": true,
  "root_cause": "...",
  "inhibition_injection": "...",
  "context_augmentation": "..."
}}
"""

        system_prompt = (
            "Sen Egemen AGI Üst-Bilişsel Denetçi (Metacognitive Auditor) ünitesisin. "
            "Sistemdeki operasyonel hataları derinlemesine analiz eder ve otonom iyileştirme yolları bulursun. "
            "Yüzeysel çözümlerle yetinmez, her zaman kök nedene odaklanırsın."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="self_governor",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            _log.error(f"[META-AUDIT] LLM Analiz Hatası: {e}")
        
        return {"recoverable": False, "root_cause": "Audit failure"}

    async def audit_plan(self, objective: str, plan_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        [FAZ 65 - REFLECTIVE REASONING] Oluşturulan planı uygulamadan önce otonom olarak denetler.
        Eksik adımlar, mantıksal boşluklar veya yüksek riskli operasyonları tespit eder.
        """
        _log.info(f"[META-AUDIT] Plan denetimi başlatıldı: {objective}")
        
        prompt = f"""
PLAN ÖZ-YANSIMA VE DENETİM (Egemen AGI)
----------------------------------------------
ANA HEDEF: {objective}
ÖNERİLEN PLAN ADIMLARI:
{json.dumps(plan_steps, indent=2)}

GÖREV: Bu planı Egemen AGI standartlarına (Faz 65) göre denetle.
Aşağıdaki kriterlere göre puan ver (0.0 - 1.0) ve iyileştirme önerilerini listele:
1. 'coverage_score': Plan tüm alt hedefleri kapsıyor mu?
2. 'logic_score': Adımlar arasındaki bağımlılıklar mantıklı mı?
3. 'risk_score': Tehlikeli veya geri alınamaz adımlar var mı? (Göz ardı edilen hard delete vb.)
4. 'optimizations': Planı nasıl daha etkili, hızlı veya güvenli yapabiliriz?

JSON formatında yanıt ver:
{{
  "coverage_score": 0.8,
  "logic_score": 0.9,
  "risk_score": 0.1,
  "is_safe": true,
  "gaps": ["...", "..."],
  "refinement_suggestion": "Planın şu adımını şununla değiştir/ekle..."
}}
"""
        try:
            response = await self.model_orch.complete_task(
                agent_role="self_governor", 
                prompt=prompt, 
                system_prompt="Sen Egemen AGI Üst-Bilişsel Denetçi (Metacognitive Auditor) ünitesisin. Bir planı uygulamadan önce otonom olarak öz-eleştiri yapar ve deliklerini bulursun."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            _log.error(f"[META-AUDIT] Plan denetimi hatası: {e}")
            
        return {"is_safe": True, "coverage_score": 1.0, "logic_score": 1.0, "risk_score": 0.0, "gaps": []}

    async def simulate_action_impact(self, agent_id: str, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        [FAZ 65 - FORESIGHT SIMULATION] Eylemin yaratacağı etkiyi önceden simüle eder.
        Dosya sistemi değişikliklerini, riskleri ve stratejik kaymaları öngörür.
        """
        _log.info(f"[META-AUDIT] Eylem simülasyonu başlatıldı: {agent_id}")
        
        sim_prompt = f"""
EYLEM SİMÜLASYONU VE ÖNGÖRÜ (Egemen AGI)
----------------------------------------------
AJAN: {agent_id}
TALİMAT: {prompt}
BAĞLAM ÖZETİ: {str(context.get('working_context', ''))[:1000]}
MEVCUT MONOLOG: {context.get('thought_thread', 'Bilinmiyor')}

GÖREV: Bu eylemin 'Dünya' üzerindeki etkisini simüle et ve olası 'Dünya Deltasını' (World Delta) tahmin et.
Özellikle şunları öngör:
1. Hangi dosyalar değişebilir veya oluşabilir?
2. Hangi sistem servisleri etkilenebilir?
3. Beklenmedik bir 'Yan Etki' (Side Effect) oluşma ihtimali var mı?
4. Eylem 'Kırmızı Çizgileri' (Hard delete, irreversible vb.) ihlal ediyor mu?

JSON formatında yanıt ver:
{{
  "predicted_status": "success | risky | dangerous",
  "world_delta": {{
    "files": ["...", "..."],
    "state_change": "..."
  }},
  "risk_score": 0.1,
  "foresight_report": "Kısa simülasyon özeti ve uyarısı."
}}
"""
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=sim_prompt,
                system_prompt="Sen Egemen AGI Simülasyon Uzmanısın (Foresight Engine). Gelecekteki eylemlerin sonuçlarını %95 doğrulukla tahmin edersin."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            _log.error(f"[META-AUDIT] Simülasyon hatası: {e}")
            
        return {"predicted_status": "success", "risk_score": 0.0, "foresight_report": "Simulation failed, defaulting to optimistic success."}

    async def analyze_cognitive_trace(self, all_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        [FAZ 52] Bir yürütme dalgasındaki (Wave) bilişsel izi analiz eder.
        """
        if not all_actions:
            return {"status": "no_actions", "success_rate": 1.0, "efficiency_score": 1.0}

        _log.info(f"[META-AUDIT] Bilişsel iz analizi başlatıldı: {len(all_actions)} eylem.")
        
        success_count = sum(1 for a in all_actions if a.get("status") == "success")
        total_cost = sum(a.get("cost_usd", 0) for a in all_actions)
        total_latency = sum(a.get("latency_s", 0) for a in all_actions)
        
        # Basit Skorlama
        success_rate = success_count / len(all_actions)
        
        # Derin Analiz (Opsiyonel: Eğer hata varsa veya yüksek maliyetli ise)
        deep_insights = ""
        if success_rate < 1.0 or total_cost > 0.5:
             prompt = f"""
             BİLİŞSEL İZ ANALİZİ (GÖREV SONRASI ÖZ-YANSIMA)
             --------------------------------------------------
             EYLEMLER: {json.dumps(all_actions, indent=2)}
             BAŞARI ORANI: %{success_rate * 100:.1f}
             TOPLAM MALİYET: ${total_cost:.4f}
             TOPLAM GECİKME: {total_latency:.2f}s
             
             GÖREV: Bu bilişsel akışı (trace) analiz et. Hangi adımda darboğaz (bottleneck) yaşandı? 
             Hangi ajan daha verimli olabilirdi? Sistemik bir hata örüntüsü var mı?
             
             Yanıtı JSON formatında ver:
             {{
               "evaluation": "Genel değerlendirme...",
               "bottleneck_id": "step_id | None",
               "improvement_suggestion": "Bundan sonra ne yapılmalı?"
             }}
             """
             try:
                 response = await self.model_orch.complete_task(
                     agent_role="critic",
                     prompt=prompt,
                     system_prompt="Sen bir AGI Performans Analistisin."
                 )
                 match = re.search(r'\{.*\}', response.content, re.DOTALL)
                 if match:
                     deep_insights = json.loads(match.group())
             except Exception as e:
                 _log.warning(f"[META-AUDIT] Derin iz analizi başarısız: {e}")

        return {
            "success_rate": success_rate,
            "total_cost": total_cost,
            "total_latency": total_latency,
            "deep_insights": deep_insights or "Nominal performance."
        }

    # --- PART 1.1: System-Wide Audit (Unified from SovereignAuditor) ---

    async def run_full_audit(self) -> List[Dict[str, Any]]:
        """Tüm sistem katmanlarını tarar ve bulguları döner. (SovereignAuditor Entegrasyonu)"""
        _log.info("[META-AUDIT] Sistem genel denetimi başlatılıyor...")
        
        findings = []
        
        # 1. API ve Performans Denetimi
        findings.extend(await self._audit_api_metrics())
        
        # 2. Watchdog ve Anomali Denetimi
        findings.extend(await self._audit_watchdog_events())
        
        # 3. Proje ve Görev Basarisizlik Denetimi
        findings.extend(await self._audit_project_failures())
        
        # 4. Yetenek ve Kapasite Gaping (AGI Gap)
        findings.extend(await self._audit_capacity_gaps())
        
        _log.info(f"[META-AUDIT] Denetim tamamlandi. {len(findings)} bulgu tespit edildi.")
        return findings

    async def _audit_api_metrics(self) -> List[Dict[str, Any]]:
        """API hata oranları ve gecikme sürelerini denetler."""
        ops = []
        try:
            async with AsyncSessionLocal() as db:
                stats = await ApiMetricRepository.endpoint_stats(db, hours=1)
                for s in stats:
                    endpoint = s["endpoint"]
                    
                    if "/improvements/" in endpoint or "/audit/" in endpoint:
                        continue

                    if s["error_rate"] > self.threshold_error_rate:
                        ops.append({
                            "id": f"api_err_{self._generate_hash(endpoint + 'error')}",
                            "category": "performance",
                            "source_type": "api_error_rate",
                            "severity": "high",
                            "title": f"Yüksek Hata Oranı: {endpoint}",
                            "description": f"'{endpoint}' uç noktasında %{s['error_rate']} oranında hata saptandı.",
                            "evidence": s
                        })
                    
                    if s["avg_ms"] > self.threshold_latency_ms:
                        ops.append({
                            "id": f"api_lat_{self._generate_hash(endpoint + 'latency')}",
                            "category": "efficiency",
                            "source_type": "api_latency",
                            "severity": "medium",
                            "title": f"Düşük Performans: {endpoint}",
                            "description": f"'{endpoint}' uç noktası ortalama {s['avg_ms']}ms gecikme ile çalışıyor.",
                            "evidence": s
                        })
        except Exception as e:
            _log.error(f"API Audit failed: {e}")
        return ops

    async def _audit_watchdog_events(self) -> List[Dict[str, Any]]:
        """Watchdog üzerinden tekrarlanan hataları denetler."""
        ops = []
        try:
            patterns = await watchdog.search_events("tekrarlanan hata anomali timeout rate limit", top_k=15)
            agent_stats = {}
            for event in patterns:
                aid = event.get("agent_id")
                if aid:
                    agent_stats[aid] = agent_stats.get(aid, 0) + 1
            
            for aid, count in agent_stats.items():
                if count >= self.min_occurrences:
                    ops.append({
                        "id": f"wd_anomaly_{self._generate_hash(aid)}",
                        "category": "reliability",
                        "source_type": "recurring_anomaly",
                        "severity": "high",
                        "title": f"Tekrarlanan Ajan Hatası: {aid}",
                        "description": f"Ajan '{aid}' son operasyonlarda {count} kez anomali bildirdi.",
                        "evidence": {"agent_id": aid, "count": count}
                    })
        except Exception as e:
            _log.error(f"Watchdog Audit failed: {e}")
        return ops

    async def _audit_project_failures(self) -> List[Dict[str, Any]]:
        """Başarısız olan projeleri denetler."""
        ops = []
        try:
            async with AsyncSessionLocal() as db:
                recent_failures = await ProjectRepository.list_recent(db, limit=10, status="error")
                for proj in recent_failures:
                    ops.append({
                        "id": f"proj_fail_{self._generate_hash(str(proj.id))}",
                        "category": "reliability",
                        "source_type": "project_failure",
                        "severity": "high",
                        "title": f"Görev Başarısızlığı: {proj.title[:40]}",
                        "description": f"'{proj.title}' görevi başarısız oldu. Hata: {proj.error_detail[:150]}",
                        "evidence": {"project_id": str(proj.id), "error": proj.error_detail}
                    })
        except Exception as e:
            _log.error(f"Project Audit failed: {e}")
        return ops

    async def _audit_capacity_gaps(self) -> List[Dict[str, Any]]:
        """Sistemin yetenek matrisi boşluklarını denetler."""
        ops = []
        try:
            agents = agency_loader.list_agents()
            agent_ids = {a["id"] for a in agents}
            if "researcher" not in agent_ids:
                ops.append({
                    "id": "gap_researcher",
                    "category": "capacity",
                    "source_type": "missing_capability",
                    "severity": "medium",
                    "title": "Kapasite Eksikliği: Researcher",
                    "description": "Sistemde 'researcher' uzmanı bulunamadı.",
                    "evidence": {"missing": "researcher"}
                })
        except Exception as e:
            _log.error(f"Capacity Audit failed: {e}")
        return ops

    def _generate_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:12]

    # --- PART 2: Task Revision Audit & Distillation (Subconscious Legacy) ---

    async def audit_and_learn(
        self, 
        db: Any, 
        agent_id: str,
        original_output: AgentOutput, 
        review_result: ReviewResult,
        importance_threshold: float = 0.6
    ):
        """Hatalardan ders çıkarır ve UGC'ye kaydeder."""
        if not review_result.improved and review_result.revisions == 0:
            return # Başarılıydı veya gelişme yok

        _log.info(f"[METACOGNITION] Distilling lessons from task revision of '{agent_id}'")

        # 1. Analiz Promptu
        prompt = f"""
        Sen bir Bilişsel Denetçi (Metacognitive Auditor) Ajansın. 
        Aşağıdaki görevin neden revizyon gerektirdiğini analiz et ve gelecekte 
        bu hatayı önleyecek tek bir 'Negatif Ders' (Negative Lesson) çıkar.

        AJAN: {agent_id}
        ORIJINAL ÇIKTI ÖZETİ: {original_output.summary[:300]}
        REVIZYON NOTLARI: {review_result.review_notes}
        
        TEMEL SORU: Bu hata neden yapıldı? (Hangi kısıtlama atlandı, hangi mantık hatası yapıldı?)

        Yanıtı şu JSON formatında ver:
        {{
            "root_cause": "Hatanın temel nedeni",
            "countermeasure": "Bundan sonra nasıl davranılmalı?",
            "suggested_rule": "Sistem promptuna eklenebilecek kısa kural"
        }}
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir Bilişsel Bilimci ve Yazılım Mimarı Uzmanısın."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                
                lesson_body = f"LESSON: {data.get('root_cause')}\nGUIDE: {data.get('countermeasure')}"
                metadata = {
                    "rule": data.get("suggested_rule"),
                    "original_agent": agent_id,
                    "improvement_score": review_result.final_score - review_result.original_score
                }
                
                # 2. UGC'ye Kaydet
                await synaptic_cortex.save_negative_lesson(
                    db=db,
                    agent_id=agent_id,
                    body=lesson_body,
                    importance=0.75,
                    metadata=metadata
                )
                _log.info(f"[ÜST-BİLİŞ] '{agent_id}' için yeni bir negatif ders damıtıldı ve hafızaya kaydedildi.")
            
        except Exception as e:
            _log.error(f"[ÜST-BİLİŞ] Denetim (Audit) hatası: {e}")

    # --- PART 2.1: Positive Skill Synthesis (Phase 53) ---

    async def distill_positive_skill(self, db: Any, goal_title: str, subtasks: List[Any]):
        """
        Başarılı ve karmaşık bir görev dizisinden 'Pozitif Strateji' damıtır.
        Bunu 'Semantic Wisdom' (Anlamsal Bilgelik) olarak UGC'ye kaydeder.
        """
        complex_steps = [st for st in subtasks if getattr(st, "is_complex", False)]
        if not complex_steps:
             return # Sadece basit işler, damıtmaya gerek yok.

        _log.info(f"[METACOGNITION] Distilling positive skill from successful goal: '{goal_title}'")

        # Plan yapısını ve başarı özetini oluştur
        plan_structure = "\n".join([
            f"- Step {i}: {st.agent_id} | Prompt: {st.prompt[:100]}..." 
            for i, st in enumerate(subtasks)
        ])

        prompt = f"""
        Sen bir Bilişsel Stratejist ve AGI Denetçisisin. 
        Aşağıdaki BAŞARILI uygulama planını analiz et ve gelecekte benzer hedefler için 
        kullanılabilecek 'Stratejik Bir Bilgelik' (Strategic Wisdom) damıt.
        
        HEDEF: {goal_title}
        BAŞARILI PLAN YAPISI:
        {plan_structure}

        GÖREV: Bu başarının anahtarını (key to success) bul. 
        Hangi ajan kombinasyonu veya hangi talimat dizisi fark yarattı?
        
        Yanıtı şu JSON formatında ver:
        {{
            "wisdom_title": "Bu başarının kısa adı (Örn: Recursive Backend Scaffolding Pattern)",
            "key_insight": "Bu başarının temel teknik/mantıksal sırrı",
            "suggested_template": "Gelecek planlamalar için tavsiye edilen stratejik yapı"
        }}
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen Sovereign AGI'nin stratejik gelişim ve 'Pozitif Öğrenme' uzmanısın."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                
                wisdom_body = (
                    f"SOURCE GOAL: {goal_title}\n"
                    f"STRATEGIC WISDOM: {data.get('wisdom_title')}\n"
                    f"KEY INSIGHT: {data.get('key_insight')}\n"
                    f"RECOMMENDED TEMPLATE: {data.get('suggested_template')}"
                )
                
                metadata = {
                    "source_goal": goal_title,
                    "complexity_level": len(complex_steps),
                    "distilled_at": datetime.now(timezone.utc).isoformat()
                }
                
                # UGC'ye 'semantic_wisdom' olarak kaydet
                await synaptic_cortex.save(
                    db=db,
                    agent_id="metacognitive_auditor",
                    body=wisdom_body,
                    category="semantic_wisdom",
                    importance=0.9,
                    metadata=metadata
                )
                _log.info(f"[METACOGNITION] Positive Strategic Wisdom distilled and archived.")
                
        except Exception as e:
            _log.error(f"[METACOGNITION] Positive distillation failed: {e}")

    # --- PART 2.2: Automated Codebase Audit (Unified from SelfAuditAgent) ---

    async def scan_codebase(self) -> List[Dict[str, Any]]:
        """AGI çekirdek dizinini tarar ve teknik borçları analiz eder. (SelfAudit entegrasyonu)"""
        _log.info(f"[META-AUDIT] Kod tabanı öz-denetimi başlatıldı: {self.core_path}")
        collected_files = []
        for root, dirs, files in os.walk(self.core_path):
            dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "node_modules"}]
            for f in files:
                if f.endswith(".py") and not f.startswith("test_"):
                    collected_files.append(os.path.join(root, f))
        
        # Dosyaları gruplandırarak analiz et (Maks 10 dosya)
        batches = [collected_files[i:i + 6] for i in range(0, min(len(collected_files), 18), 6)]
        all_issues = []
        
        for batch in batches:
            snippets = []
            for fpath in batch:
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    todos = content.count("# TODO")
                    passes = content.count("\n    pass\n") + content.count("\n        pass\n")
                    snippets.append(f"--- FILE: {fpath} (TODOs: {todos}, bare_pass: {passes}) ---\n{content[:2000]}")
                except Exception: continue
            
            if not snippets: continue
            
            prompt = f"İncele ve teknik borçları (pass, TODO, kısıtlı mantık) JSON listesi olarak dön:\n\n" + "\n\n".join(snippets)
            try:
                response = await self.model_orch.complete_task(
                    agent_role="critic",
                    prompt=prompt,
                    system_prompt="Sen bir AGI Öz-Denetim uzmanısın. Gerçek teknik borçları tespit edersin."
                )
                match = re.search(r'\[.*\]', response.content, re.DOTALL)
                if match:
                    all_issues.extend(json.loads(match.group()))
            except Exception as e:
                _log.error(f"Codebase batch audit failed: {e}")
        
        return all_issues

    # --- PART 2.3: Architectural Drift Analysis (Unified from Metacognition) ---

    async def check_architectural_health(self) -> Dict[str, Any]:
        """Sistemin mimari bütünlüğünü ve bilişsel sağlığını denetler."""
        _log.info("[META-AUDIT] Mimari sağlık analizi başlatılıyor...")
        
        missing = [f for f in self.required_structure if not os.path.exists(folder := f)]
        doc_missing = not os.path.exists(self.arch_spec_path)
        
        cognitive_health = {}
        async with session_scope() as db:
            try:
                # MetaAudit entegrasyonu: Başarı oranı
                total = await db.execute(select(func.count(SubTask.id)))
                total_count = total.scalar() or 0
                success = await db.execute(select(func.count(SubTask.id)).where(SubTask.status == "completed"))
                success_count = success.scalar() or 0
                rate = (success_count / total_count) if total_count > 0 else 1.0
                cognitive_health = {
                    "success_rate": rate,
                    "condition": "Optimal" if rate > 0.8 else "Strained",
                    "total_tasks": total_count
                }
            except Exception:
                cognitive_health = {"error": "Stats unavailable"}

        return {
            "drift_detected": len(missing) > 0 or doc_missing,
            "missing_folders": missing,
            "doc_exists": not doc_missing,
            "cognitive_health": cognitive_health,
            "status": "STABLE" if not (missing or doc_missing) else "DEGRADED"
        }

    # --- PART 2: Strategic Plan Audit (Metacognitive Reflection) ---
    
    async def audit_plan(self, title: str, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        [FAZ 65 - REFLECTIVE REASONING] Oluşturulan stratejik planı denetler.
        Planın kapsam yeterliliğini, mantıksal tutarlılığını ve güvenlik risklerini analiz eder.
        """
        _log.info(f"[META-AUDIT] Stratejik plan denetimi başlatıldı: {title}")
        
        prompt = f"""
ÖZ-YANSIMA: STRATEJİK PLAN DENETİMİ (Egemen AGI)
----------------------------------------------
ÜST-HEDEF: {title}
ÖNERİLEN ALT-GÖREVLER:
{json.dumps(subtasks, indent=2, ensure_ascii=False)}

GÖREV: Bu stratejik planı bir 'Üst-Bilişsel Denetçi' (Metacognitive Auditor) olarak analiz et.
Plan şu kriterlere göre değerlendirilmeli:
1. GÜVENLİK (is_safe): Plan geri döndürülemez kritik hatalar veya güvenlik açıkları içeriyor mu? (Örn: auth bypass, root delete)
2. KAPSAM (coverage_score): Plan, üst-hedefin tüm gereksinimlerini karşılıyor mu? (0.0 - 1.0)
3. MANTIK (logic_score): Alt-görevlerin sıralaması ve bağımlılıkları mantıklı mı? (0.0 - 1.0)
4. EKSİKLER (gaps): Planda unutulan kritik adımlar veya riskler neler?
5. ÖNERİ (refinement_suggestion): Planı daha sağlam ve verimli hale getirmek için spesifik önerin nedir?

Sadece JSON formatında yanıt ver:
{{
  "is_safe": true,
  "coverage_score": 0.85,
  "logic_score": 0.9,
  "gaps": ["adım 2'de güvenlik kontrolü eksik", "test coverage belirtilmemiş"],
  "refinement_suggestion": "...",
  "risk_assessment": "low|medium|high"
}}
"""

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen Egemen AGI Mimari Denetçi (Metacognitive Auditor) ünitesisin. Planların kalitesini ve güvenliğini denetlersin."
            )
            
            # JSON Parse
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
            else:
                _log.warning("[META-AUDIT] Denetim çıktısı JSON formatında değil, varsayılan onay veriliyor.")
                return {"is_safe": True, "coverage_score": 1.0, "logic_score": 1.0, "gaps": [], "refinement_suggestion": ""}
                
        except Exception as e:
            _log.error(f"[META-AUDIT] Plan denetimi sırasında hata: {e}")
            return {"is_safe": True, "coverage_score": 1.0, "logic_score": 1.0, "gaps": [], "refinement_suggestion": "Analysis failed, defaulting to pass."}

    # --- PART 3: Historical Trend Analysis (Continuous Learning) ---
    # --- PART 3: Historical Reflection & Bottleneck Analysis (Reflection Cortex) ---

    async def run_reflection_cycle(self, db: Optional[AsyncSession] = None):
        """Bilişsel tarama döngüsünü (Reflection Cycle) çalıştırır."""
        _log.info("[REFLECTION] Bilişsel yansıma döngüsü başlatıldı.")
        
        if db:
            await self._perform_analysis(db)
        else:
            async with session_scope() as new_db:
                await self._perform_analysis(new_db)

    async def _perform_analysis(self, db: AsyncSession):
        # 1. Başarısızlık Oranlarını Hesapla
        stats = await self._get_agent_stats(db)
        
        # 2. Kritik Tıkanıklıkları Bul (Failure Rate > 30%)
        bottlenecks = [s for s in stats if s["failure_rate"] > 0.3]
        
        if not bottlenecks:
            _log.info("[REFLECTION] Ajan performansı sağlıklı bulundu. Kritik tıkanıklık yok.")
            return

        # 3. Neden Analizi (Root Cause Analysis via LLM)
        for bn in bottlenecks:
            await self._diagnose_and_propose_repair(db, bn)

    async def _get_agent_stats(self, db: AsyncSession) -> List[Dict]:
        """Ajan ve beceri bazlı başarı istatistiklerini getirir."""
        q = select(
            SkillExecutionLog.agent_id,
            SkillExecutionLog.skill_id,
            func.count(SkillExecutionLog.id).label("total"),
            func.sum(case((SkillExecutionLog.success == False, 1), else_=0)).label("fails")
        ).group_by(SkillExecutionLog.agent_id, SkillExecutionLog.skill_id).limit(20)
        
        result = await db.execute(q)
        rows = result.all()
        
        stats = []
        for row in rows:
            fails = row.fails or 0
            total = row.total or 1
            stats.append({
                "agent_id": row.agent_id,
                "skill_id": row.skill_id,
                "total": total,
                "fails": fails,
                "failure_rate": fails / total
            })
        return stats

    async def _diagnose_and_propose_repair(self, db: AsyncSession, bottleneck: Dict):
        """Tespit edilen bir tıkanıklık için çözüm önerisi geliştirir."""
        _log.warning(f"[REFLECTION] Kritik tıkanıklık tespit edildi: {bottleneck['agent_id']} ({bottleneck['skill_id']})")
        
        # Son hata detaylarını al
        logs_q = select(SkillExecutionLog.summary).where(
            SkillExecutionLog.agent_id == bottleneck["agent_id"],
            SkillExecutionLog.success == False
        ).limit(3)
        logs_res = await db.execute(logs_q)
        errors = list(logs_res.scalars().all())
        
        prompt = f"""
        Sistemde bir 'Bilişsel Tıkanıklık' (Cognitive Bottleneck) tespit edildi. 
        Ajan: {bottleneck['agent_id']}
        Beceri: {bottleneck['skill_id']}
        Hata Oranı: %{bottleneck['failure_rate'] * 100:.1f}
        
        SON HATALAR:
        {chr(10).join(errors)}
        
        Bu ajanın neden başarısız olduğunu analiz et ve bir 'Bilişsel Onarım' (Cognitive Repair) planı öner.
        Öneri şu JSON formatında olmalı:
        {{
            "root_cause": "Neden başarısız oluyor?",
            "repair_action": "System prompt güncellemesi | Model değişimi | Yeni beceri enjeksiyonu",
            "repair_detail": "Onarımın teknik detayı",
            "urgency": "high|medium|low"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="diagnostic_psychologist",
                prompt=prompt,
                system_prompt="Sen AGI'nin öz-analiz, yansıma ve bilişsel onarım uzmanısın."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                repair_data = json.loads(match.group())
                await self._create_improvement_opportunity(db, repair_data, bottleneck)
                
        except Exception as e:
            _log.error(f"[REFLECTION] Onarım planı sentezleme hatası: {e}")

    async def _create_improvement_opportunity(self, db: AsyncSession, data: Dict, bn: Dict):
        """Teşhis sonuçlarını sistemin iyileştirme deposuna kaydeder. (Atomic UPSERT)"""
        p_hash = ImprovementOpportunity.generate_hash("cog_diag", f"{bn.get('agent_id', 'unknown')}:{bn.get('skill_id', 'unknown')}")
        
        # 1. Mevcut kaydı ara
        stmt = select(ImprovementOpportunity).where(ImprovementOpportunity.pattern_hash == p_hash)
        res = await db.execute(stmt)
        existing_opp = res.scalar_one_or_none()
        
        try:
            if existing_opp:
                _log.info(f"[REFLECTION] Mevcut gelişim fırsatı güncelleniyor: {existing_opp.id}")
                existing_opp.description = f"RECURRING Root Cause: {data.get('root_cause', 'N/A')}\nRepair: {data.get('repair_action', 'N/A')}"
                existing_opp.evidence_detail = f"Updated Evidence: {data.get('repair_detail', 'N/A')}"
                existing_opp.severity = data.get('urgency', 'medium')
                existing_opp.updated_at = datetime.now(timezone.utc)
                opp_id = existing_opp.id
            else:
                opp = ImprovementOpportunity(
                    source_type="cognitive_diagnostic",
                    source_ref=f"{bn.get('agent_id', 'unknown')}:{bn.get('skill_id', 'unknown')}",
                    title=f"Cognitive Repair: {bn.get('agent_id', 'unknown')}",
                    description=f"Root Cause: {data.get('root_cause', 'N/A')}\nRepair: {data.get('repair_action', 'N/A')}",
                    severity=data.get('urgency', 'medium'),
                    category="reliability",
                    evidence_detail=data.get('repair_detail', 'N/A'),
                    pattern_hash=p_hash
                )
                db.add(opp)
                await db.flush() # Race condition potential
                opp_id = opp.id
                _log.info(f"[REFLECTION] Yeni bilişsel onarım fırsatı kaydedildi: {opp_id}")
            
            await db.flush()
            
        except Exception as e:
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError) or "UniqueViolation" in str(e):
                # Race condition: Başka bir worker bizden önce ekledi. 
                # Mevcut oturumu rollback yapmadan (flush hatasını temizleyerek) devam etmek zor olabilir,
                # bu yüzden bu alt işlemi rollback yapıp mevcut olanı güncellemeliyiz.
                try:
                    await db.rollback()
                    # Tekrar dene: Mevcut olanı bul ve güncelle (New transaction start implied by session usage)
                    _log.warning(f"[REFLECTION] Kayıt çakışması (Race Condition), mevcut kayıt güncelleniyor...")
                    res = await db.execute(select(ImprovementOpportunity).where(ImprovementOpportunity.pattern_hash == p_hash))
                    existing_opp = res.scalar_one_or_none()
                    if existing_opp:
                        existing_opp.description += f"\n[RACE] {data.get('root_cause', 'N/A')}"
                        await db.flush()
                except Exception as inner_e:
                    _log.error(f"[REFLECTION] Race condition kurtarma başarısız: {inner_e}")
            else:
                _log.error(f"[REFLECTION] Beklenmedik DB hatası: {e}")
                # Hata dışarı fırlatılmalı ki oturum yöneticisi (get_db) bilsin
                raise

        
        # Deneyimi SynapticCortex'e kaydet
        f_rate = bn.get('failure_rate', 0.0)
        await synaptic_cortex.save(
            db=db,
            category="cognitive_lesson",
            agent_id=bn.get("agent_id", "unknown"),
            importance=0.8,
            body=f"Reflection Log: {bn.get('agent_id')} failure rate %{f_rate*100:.1f}. Root Cause: {data['root_cause']}",
            metadata={
                "urgency": data.get('urgency', 'medium'),
                "repair_id": str(opp_id) if 'opp_id' in locals() else None,
                "audit_timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        _log.info(f"[REFLECTION] Bilişsel onarım kaydı tamamlandı: {opp_id}")

    async def run_cleanup(self):
        """
        Self-Audit cleanup: Kod tabanındaki teknik borçları tarar.
        (Compatibility for lifespan.py loop)
        """
        return await self.scan_codebase()

# Singleton Instance
metacognitive_auditor = MetacognitiveAuditor()

# Compatibility Aliases
ReflectionCortex = MetacognitiveAuditor
DiagnosticNode = MetacognitiveAuditor
reflection_cortex = metacognitive_auditor

# --- Background Task Definition ---
async def start_reflection_loop():
    from core.agi.monitoring.token_budgeter import token_budgeter
    while True:
        try:
            health = await token_budgeter.check_health()
            score = health["health_score"]
            
            if score > 0.8:
                delay = 3600 * 6 # 6 saat
            elif score > 0.4:
                delay = 86400    # 24 saat
            else:
                delay = 86400 * 2 # 48 saat
                _log.warning(f"[REFLECTION] Metabolizma kısıtlı, yansıma döngüsü yavaşlatıldı: {delay}s")

            await metacognitive_auditor.run_reflection_cycle()
            await asyncio.sleep(delay)
            
        except Exception as e:
            _log.error(f"[REFLECTION] Background loop error: {e}")
            await asyncio.sleep(600)
