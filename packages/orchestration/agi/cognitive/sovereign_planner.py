import json
import logging
from typing import List, Dict, Any, Optional
from llm.model_orchestrator import ModelOrchestrator
from packages.orchestration.agi.task_governance import GovernedTask, GovernanceStatus, SubTask, TaskStatus
import uuid
import uuid
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from db.session import get_db

_log = logging.getLogger("agi_sovereign_planner")

class SovereignPlanner:
    """
    Cognitive Layer 34: Sovereign Planning (Egemen Planlama).
    Statik planlama yerine, hedefe özel ajan seçimi ve DAG oluşturma yapar.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def decompose(self, title: str, description: str, available_agents: List[Dict[str, Any]], affective_state: Optional[Dict[str, float]] = None) -> List[SubTask]:
        """
        Hedefi analiz eder ve gerekli ajanlardan oluşan bir plan (SubTask listesi) döner.
        Bilişsel Eşik: AffectiveCore durumuna göre planın risk/güvenlik dengesi ayarlanır.
        """
        _log.info(f"[PLANNER] Hedef analiz ediliyor: {title}")
        
        # Faz 46: Stratejik Geri Çağırma (Hafızadan başarılı planları ve BİLGELİKLERİ bul)
        wisdom_brief = ""
        try:
            async with get_db() as db:
                # 1. Geçmişteki başarılı görevleri ara
                memories = await synaptic_cortex.search(db, f"{title} {description}", category="episode", top_k=3)
                
                # 2. Faz 46: Sentezlenmiş BİLGELİKLERİ (Wisdom) ara
                wisdoms = await synaptic_cortex.search(db, f"{title} {description}", category="semantic_wisdom", top_k=2)
                
                past_plans_brief = "\n### GEÇMİŞ BAŞARILI PLANLAR (REFERANS):\n"
                if memories:
                    for m in memories:
                        past_plans_brief += f"- {m.get('body', '')[:200]}...\n"
                else:
                    past_plans_brief += "- Benzer geçmiş görev bulunamadı.\n"
                
                if wisdoms:
                    wisdom_brief = "\n### ÖĞRENİLMİŞ BİLGELİK VE PRENSİPLER (STRATEJİK):\n"
                    for w in wisdoms:
                        wisdom_brief += f"- {w.get('body', '')}\n"
        except Exception as e:
            _log.warning(f"[DECOMPOSER] Stratejik hafıza (Wisdom) araması başarısız: {e}")
        
        # Faz 35: Affective Steering
        affect_summary = ""
        if affective_state:
            caution = affective_state.get("caution", 0.5)
            stress = affective_state.get("internal_stress", 0.2)
            curiosity = affective_state.get("curiosity", 0.5)
            
            if caution > 0.7 or stress > 0.6:
                affect_summary = "\n[BİLİŞSEL MOD: CAUTIOUS] Sistem şu an yüksek stresli veya ihtiyatlı. Planın GÜVENLİK, TEST ve DOĞRULAMA adımlarına ağırlık ver."
            elif curiosity > 0.8:
                affect_summary = "\n[BİLİŞSEL MOD: EXPLORATORY] Sistem meraklı ve keşif odaklı. Daha inovatif ve kapsamlı bir çözüm planla."
            else:
                 affect_summary = "\n[BİLİŞSEL MOD: BALANCED] Dengeli bir planlama yap."

        agent_briefs = "\n".join([
            f"- {a.id}: {a.role} ({a.name})" 
            for a in available_agents
        ])


        prompt = f"""
        Aşağıdaki hedefi (Goal) gerçekleştirmek için MODÜLER, VERİMLİ ve ADIM ADIM bir uygulama planı oluştur.
        Sadece ihtiyacın olan ajanları seç. Her adımı bir önceki adımın çıktısına bağımlı hale getirebilirsin.
        {affect_summary}
        {past_plans_brief}
        {wisdom_brief}
        
        HEDEF: {title}
        AÇIKLAMA: {description}
        
        KULLANILABİLİR AJANLAR:
        {agent_briefs}
        
        Yanıtı SADECE aşağıdaki JSON formatında ver:
        {{
            "reasoning": "Planın stratejik gerekçesi ve bilişsel modun plana etkisi",
            "plan": [
                {{
                    "step_id": "step_0",
                    "agent_id": "seçilen_ajan_id",
                    "prompt": "Ajana verilecek spesifik talimat. Ne yapmalı ve neyi çıktı vermeli?",
                    "dependencies": []
                }},
                {{
                    "step_id": "step_1",
                    "agent_id": "başka_ajan_id",
                    "prompt": "İkinci adım talimatı.",
                    "dependencies": ["step_0"],
                    "is_complex": true,
                    "complexity_reasoning": "Neden bu adımın daha derin bir alt-plan gerektirdiğine dair gerekçe."
                }}
            ]
        }}
        
        NOT: Eğer bir adım çok geniş kapsamlıysa (örn: "Tüm backend'i yaz", "Veritabanını tasarla"), 'is_complex' değerini true yap.
        Bağımsız adımlar için dependencies listesini boş bırak. Bağımlı adımlarda bağımlı olduğu step_id'leri yaz.
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Stratejistisin. Karmaşık hedefleri en az adımda, en yüksek kalitede çözecek dinamik planlar oluşturursun."
            )
            
            data = self._parse_json(response.content)
            if not data or "plan" not in data:
                _log.warning("[DECOMPOSER] Plan ayrıştırılamadı. Statik fallback'e dönülüyor.")
                return []

            # --- [FIX-8] DAG dependencies artık gerçekten parse ediliyor ---
            subtasks: List[SubTask] = []
            step_id_map: Dict[str, str] = {}  # step_id -> SubTask.id

            for i, step in enumerate(data["plan"]):
                step_id = step.get("step_id", f"step_{i}")
                st_id = str(uuid.uuid4())[:8]
                step_id_map[step_id] = st_id

                st = SubTask(
                    id=st_id,
                    agent_id=step.get("agent_id", "architect"),
                    prompt=step.get("prompt", ""),
                    status=TaskStatus.PENDING
                )

                # Bağımlılıkları SubTask ID'ye çevir
                raw_deps = step.get("dependencies", [])
                resolved_deps = []
                for dep_key in raw_deps:
                    if dep_key in step_id_map:
                        resolved_deps.append(step_id_map[dep_key])
                    else:
                        resolved_deps.append(dep_key)  # Henüz bilinmiyorsa ham key sakla
                st.dependencies = resolved_deps
                
                # Faz 51: Recursive Info
                st.is_complex = step.get("is_complex", False)
                st.complexity_reasoning = step.get("complexity_reasoning", "")

                subtasks.append(st)

            _log.info(
                f"[DECOMPOSER] Dinamik DAG planı oluşturuldu. "
                f"Adım: {len(subtasks)}, "
                f"Bağımlılıklı: {sum(1 for s in subtasks if s.dependencies)}"
            )
            return subtasks

        except Exception as e:
            _log.error(f"[PLANNER] Dekompozisyon hatası: {e}")
            return [SubTask(id=str(uuid.uuid4())[:8], agent_id="architect", prompt=f"Fallback: {title}", status=TaskStatus.PENDING)]

    def get_execution_waves(self, subtasks: List[SubTask]) -> List[List[SubTask]]:
        """
        [FIX-8] DAG'ı "yürütme dalgası" gruplarına dönüştürür.
        Her dalga, bir önceki dalga tamamlanmadan çalıştırılamayan bağımlı adımları içerir.
        Bağımsız adımlar aynı dalgada paralel çalışabilir.

        Örnek:
          step_0 (bağımsız) → step_2 (step_0'a bağımlı) → step_3 (step_2'ye bağımlı)
          step_1 (bağımsız) ↗
          
          Dalga 0: [step_0, step_1]  (paralel)
          Dalga 1: [step_2]          (step_0 bitti sonra)
          Dalga 2: [step_3]          (step_2 bitti sonra)
        """
        id_set = {s.id for s in subtasks}
        id_to_subtask = {s.id: s for s in subtasks}
        completed: set = set()
        waves: List[List[SubTask]] = []
        remaining = list(subtasks)

        while remaining:
            # Bu turdaki çalıştırılabilir adımlar: tüm bağımlılıkları tamamlanmış olanlar
            ready = [
                s for s in remaining
                if all(dep in completed for dep in (s.dependencies or []) if dep in id_set)
            ]
            if not ready:
                # Çözülemeyen bağımlılık — kalan adımları doğrudan ekle
                _log.warning(f"[DECOMPOSER] Çözülemeyen DAG bağımlılığı. Kalan {len(remaining)} adım sıralı ekleniyor.")
                waves.append(remaining)
                break
            waves.append(ready)
            for r in ready:
                completed.add(r.id)
                remaining.remove(r)

        _log.info(f"[DECOMPOSER] DAG çözümlendi: {len(waves)} yürütme dalgası.")
        return waves

    def _parse_json(self, text: str) -> Optional[Dict]:
        import re
        _log.debug(f"[PLANNER] Parsing JSON from text length: {len(text)}")
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                _log.debug(f"[PLANNER] JSON successfully parsed. Keys: {list(data.keys())}")
                return data
            except Exception as e:
                _log.error(f"[PLANNER] JSON Load Error: {e} | Text: {text[:200]}")
                pass
        else:
            _log.error(f"[PLANNER] No JSON block found in text: {text[:200]}")
        return None

# Singleton
sovereign_planner = SovereignPlanner()

