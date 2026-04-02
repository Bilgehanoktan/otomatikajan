import asyncio
import os
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from db.session import session_scope
from db.models import SkillExecutionLog, ImprovementOpportunity, Project
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from quality.reviewer import ReviewResult
from core.system_indexer import SystemIndexer
from quality.output_schema import AgentOutput

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
        p_hash = ImprovementOpportunity.generate_hash("cog_diag", f"{bn['agent_id']}:{bn['skill_id']}")
        
        # 1. Mevcut kaydı ara
        stmt = select(ImprovementOpportunity).where(ImprovementOpportunity.pattern_hash == p_hash)
        res = await db.execute(stmt)
        existing_opp = res.scalar_one_or_none()
        
        try:
            if existing_opp:
                _log.info(f"[REFLECTION] Mevcut gelişim fırsatı güncelleniyor: {existing_opp.id}")
                existing_opp.description = f"RECURRING Root Cause: {data['root_cause']}\nRepair: {data['repair_action']}"
                existing_opp.evidence_detail = f"Updated Evidence: {data['repair_detail']}"
                existing_opp.severity = data['urgency']
                existing_opp.updated_at = datetime.now(timezone.utc)
                opp_id = existing_opp.id
            else:
                opp = ImprovementOpportunity(
                    source_type="cognitive_diagnostic",
                    source_ref=f"{bn['agent_id']}:{bn['skill_id']}",
                    title=f"Cognitive Repair: {bn['agent_id']}",
                    description=f"Root Cause: {data['root_cause']}\nRepair: {data['repair_action']}",
                    severity=data['urgency'],
                    category="reliability",
                    evidence_detail=data['repair_detail'],
                    pattern_hash=p_hash
                )
                db.add(opp)
                await db.flush() # Burada hata alabilir (Race Condition)
                opp_id = opp.id
                _log.info(f"[REFLECTION] Yeni bilişsel onarım fırsatı kaydedildi: {opp_id}")
            
            await db.flush()
            
        except Exception as e:
            from sqlalchemy.exc import IntegrityError
            if "UniqueViolationError" in str(e) or isinstance(e, IntegrityError):
                await db.rollback() # Bu alt-oturum işlemini geri al
                _log.warning(f"[REFLECTION] Kayıt çakışması tespit edildi (Race Condition), güncelleniyor...")
                # Tekrar dene: Mevcut olanı bul ve güncelle
                res = await db.execute(select(ImprovementOpportunity).where(ImprovementOpportunity.pattern_hash == p_hash))
                existing_opp = res.scalar_one_or_none()
                if existing_opp:
                    existing_opp.description += f"\n[RACE] {data['root_cause']}"
                    await db.flush()
                    opp_id = existing_opp.id
                else:
                    raise # Beklenmedik durum
            else:
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
