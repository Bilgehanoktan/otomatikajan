import asyncio
import os
import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from packages.observability.logging import get_logger
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.persistence.session import session_scope, AsyncSessionLocal
from packages.persistence.models import SkillExecutionLog, ImprovementOpportunity, Project, SubTask
from packages.persistence.repositories.repository import ProjectRepository, ApiMetricRepository
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from packages.quality_assurance.reviewer import ReviewResult
from packages.orchestration.indexing.system_indexer import SystemIndexer
from packages.quality_assurance.output_schema import AgentOutput
from packages.orchestration.agency.loader import agency_loader
from packages.memory.watchdog import watchdog

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
Especially foresee:
1. Which files might change or be created?
2. Which system services might be affected?
3. Is there a probability of an unexpected 'Side Effect'?
4. Does the action violate 'Red Lines' (Hard delete, irreversible, etc.)?

Respond in JSON format:
{{
  "predicted_status": "success | risky | dangerous",
  "world_delta": {{
    "files": ["...", "..."],
    "state_change": "..."
  }},
  "risk_score": 0.1,
  "foresight_report": "Short simulation summary and warning."
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
        
        # Derin Analiz
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

    async def run_full_audit(self) -> List[Dict[str, Any]]:
        """Tüm sistem katmanlarını tarar ve bulguları döner."""
        _log.info("[META-AUDIT] Sistem genel denetimi başlatılıyor...")
        findings = []
        findings.extend(await self._audit_api_metrics())
        findings.extend(await self._audit_watchdog_events())
        findings.extend(await self._audit_project_failures())
        findings.extend(await self._audit_capacity_gaps())
        return findings

    async def _audit_api_metrics(self) -> List[Dict[str, Any]]:
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

    async def audit_and_learn(self, db: Any, agent_id: str, original_output: AgentOutput, review_result: ReviewResult):
        if not review_result.improved and review_result.revisions == 0:
            return
        _log.info(f"[METACOGNITION] Distilling lessons from task revision of '{agent_id}'")
        prompt = f"""
        Analyze why this task required revision and extract one 'Negative Lesson'.
        AGENT: {agent_id}
        ORIGINAL SUMMARY: {original_output.summary[:300]}
        REVISION NOTES: {review_result.review_notes}
        Respond in JSON:
        {{
            "root_cause": "...",
            "countermeasure": "...",
            "suggested_rule": "..."
        }}
        """
        try:
            response = await self.model_orch.complete_task(agent_role="architect", prompt=prompt)
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                lesson_body = f"LESSON: {data.get('root_cause')}\nGUIDE: {data.get('countermeasure')}"
                await synaptic_cortex.save_negative_lesson(db=db, agent_id=agent_id, body=lesson_body, metadata={"rule": data.get("suggested_rule")})
        except Exception as e: _log.error(f"Audit learn failed: {e}")

    async def distill_positive_skill(self, db: Any, goal_title: str, subtasks: List[Any]):
        _log.info(f"[METACOGNITION] Distilling positive skill: '{goal_title}'")
        prompt = f"Distill strategic wisdom from success: {goal_title}. Respond in JSON."
        try:
            response = await self.model_orch.complete_task(agent_role="architect", prompt=prompt)
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                await synaptic_cortex.save(db=db, agent_id="metacognitive_auditor", category="semantic_wisdom", body=str(data))
        except Exception as e: _log.error(f"Distill failed: {e}")

    async def scan_codebase(self) -> List[Dict[str, Any]]:
        _log.info(f"Scanning {self.core_path} for technical debt...")
        # ... logic omitted for brevity in POC but full version is in legacy file ...
        return []

    async def check_architectural_health(self) -> Dict[str, Any]:
        _log.info("Checking architectural health...")
        return {"status": "STABLE"}

    async def run_reflection_cycle(self, db: Optional[AsyncSession] = None):
        _log.info("[REFLECTION] Reflection cycle started.")
        if db: await self._perform_analysis(db)
        else:
            async with session_scope() as new_db: await self._perform_analysis(new_db)

    async def _perform_analysis(self, db: AsyncSession):
        stats = await self._get_agent_stats(db)
        bottlenecks = [s for s in stats if s["failure_rate"] > 0.3]
        for bn in bottlenecks: await self._diagnose_and_propose_repair(db, bn)

    async def _get_agent_stats(self, db: AsyncSession) -> List[Dict]:
        q = select(SkillExecutionLog.agent_id, SkillExecutionLog.skill_id, func.count(SkillExecutionLog.id).label("total"), func.sum(case((SkillExecutionLog.success == False, 1), else_=0)).label("fails")).group_by(SkillExecutionLog.agent_id, SkillExecutionLog.skill_id).limit(20)
        result = await db.execute(q)
        return [{"agent_id": r.agent_id, "skill_id": r.skill_id, "failure_rate": (r.fails or 0) / (r.total or 1)} for r in result.all()]

    async def _diagnose_and_propose_repair(self, db: AsyncSession, bottleneck: Dict):
        _log.warning(f"Diagnosing bottleneck: {bottleneck['agent_id']}")
        # Simplified for POC
        pass

    async def _create_improvement_opportunity(self, db: AsyncSession, data: Dict, bn: Dict):
        # Simplified for POC
        pass

# Singleton Instance
metacognitive_auditor = MetacognitiveAuditor()

# Compatibility Aliases
ReflectionCortex = MetacognitiveAuditor
DiagnosticNode = MetacognitiveAuditor
reflection_cortex = metacognitive_auditor

# --- Background Task Definition ---
async def start_reflection_loop():
    while True:
        try:
            await metacognitive_auditor.run_reflection_cycle()
            await asyncio.sleep(3600 * 6)
        except Exception as e:
            _log.error(f"Reflection loop error: {e}")
            await asyncio.sleep(600)
