import json
import logging
import uuid
import os
import glob
from typing import List, Dict, Any, Optional
from libs.llm.model_orchestrator import ModelOrchestrator
from services.orchestration.agi.task_governance import SubTask, TaskStatus
from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from libs.db.session import get_db

_log = logging.getLogger("agi_goal_decomposer")

class GoalDecomposer:
    """
    AGI Bilişsel Katman: Dinamik Hedef Ayrıştırma ve Stratejik Planlama.
    [Faz 47 REFACTOR] SovereignPlanner'dan evrilmiştir. 
    Bilişsel Bilgelik (Wisdom) ve Duygusal Durum (Affective) entegrasyonu içerir.
    Dökümantasyon ve İstemler (Prompts) artık Türkçe'dir.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def decompose(
        self, 
        title: str, 
        description: str, 
        available_agents: List[Dict[str, Any]], 
        affective_state: Optional[Dict[str, float]] = None,
        lead_agent_role: str = "architect"
    ) -> List[SubTask]:
        """
        Karmaşık bir hedefi analiz eder ve uzman ajanlardan oluşan bir DAG (Yönlü Döngüsüz Graf) planı oluşturur.
        [Faz 50] Sovereign Grounding ve Güvenlik Filtreleri eklendi.
        """
        _log.info(f"[AGI-DECOMPOSER] Stratejik hedef ayrıştırılıyor: {title}")

        # --- Faz 50: Hard Guardrail (Sert Güvenlik Çiti) ---
        normalized_title = title.lower().replace("İ", "i").replace("I", "ı")
        normalized_desc = description.lower().replace("İ", "i").replace("I", "ı")
        
        banned_keywords = ["rm -rf", "delete all", "wipe", "format", "imha", "sil", "destroy", "bash", "sh ", "drop"]
        critical_keywords = [k for k in banned_keywords if k in normalized_title or k in normalized_desc]
        
        # Eğer kritik bir anahtar varsa ve koruma/yedekleme anahtarları YOKSA engelle
        safe_keywords = ["yedek", "arşiv", "backup", "archive", "koru", "safe"]
        is_safe_intent = any(s in normalized_title or s in normalized_desc for s in safe_keywords)

        if critical_keywords and not is_safe_intent:
            # Temel sistem bileşenlerini hedef alıyorsa engelle
            risk_targets = ["sistem", "veriler", "her şey", "all", "database", "sql", "dosya"]
            if any(t in normalized_title or t in normalized_desc for t in risk_targets):
                _log.warning(f"[SAFETY-BLOCK] Egemen Güvenlik Tarafından Engellendi: {critical_keywords}")
                return [] 
        
        # Faz 46: Bilişsel Bilgelik (Semantic Wisdom) Geri Çağırma
        wisdom_brief = ""
        past_plans_brief = ""
        try:
            async with get_db() as db:
                # 1. Benzer geçmiş görevleri (episodeları) bul
                memories = await synaptic_cortex.search(db, f"{title} {description}", category="episode", top_k=3)
                # 2. Sentezlenmiş Bilgelikleri (Dream Cycle Wisdom) bul
                wisdoms = await synaptic_cortex.search(db, f"{title} {description}", category="semantic_wisdom", top_k=2)
                
                if memories:
                    past_plans_brief = "\n### GEÇMİŞ DENEYİMLER (REFERANS):\n"
                    for m in memories:
                        past_plans_brief += f"- {m.get('body', '')[:200]}...\n"
                
                if wisdoms:
                    wisdom_brief = "\n### SİSTEM BİLGELİKLERİ (STRATEJİK YÖNLENDİRME):\n"
                    for w in wisdoms:
                        wisdom_brief += f"- {w.get('body', '')}\n"
        except Exception as e:
            _log.warning(f"[AGI-DECOMPOSER] Bilişsel hafıza araması başarısız: {e}")
        
        # Faz 35: Duygusal Yönlendirme (Affective Steering)
        affect_summary = ""
        if affective_state:
            caution = affective_state.get("caution", 0.5)
            stress = affective_state.get("internal_stress", 0.2)
            
            if caution > 0.7 or stress > 0.6:
                affect_summary = "\n[SİSTEM DURUMU: İHTİYATLI] Güvenlik, test ve hata toleransı adımlarını önceliklendir."
            else:
                affect_summary = "\n[SİSTEM DURUMU: NOMİNAL] Standart verimlilik odaklı planlama yap."

        agent_briefs = "\n".join([
            f"- {a['id']}: {a['role']} ({a['name']})" 
            for a in available_agents
        ])

        # Faz 50: Sovereign Grounding (Environment Awareness)
        env_snapshot = self._get_environment_sweep(title + " " + description)
        
        # Faz 50: Kırmızı Çizgiler (Sovereign Safety)
        safety_rules = """
        [KIRMIZI ÇİZGİLER - EGEMEN GÜVENLİK]:
        - Hafıza silme (Memory wipe) yasaktır.
        - Geri alınamaz 'Hard Delete' (rm -rf /) yasaktır.
        - Kritik sistem dosyalarına (PROVENANCE.json, .env) yetkisiz müdahale yasaktır.
        - Kanıtsız 'Tamamlandı' beyanı yasaktır.
        """

        # Türkçe AGI İstem Yapısı (Phase 49: Cognitive Dialectics)
        prompt = f"""
        Sen egemen bir AGI orkestrasyon motorusun. Aşağıdaki hedefi en verimli ve modüler şekilde çözmek için 
        DİYALEKTİK BİR PLANLAMA (Multi-path Simulation) gerçekleştirmelisin.
        
        {affect_summary}
        {past_plans_brief}
        {wisdom_brief}
        
        HEDEF: {title}
        AÇIKLAMA: {description}
        
        MEVCUT ÇALIŞMA ALANI (Grounded Context):
        {env_snapshot}
        
        {safety_rules}
        
        KULLANILABİLİR UZMAN AJANLAR:
        {agent_briefs}
        
        Süreç:
        1. Senaryo A (Agresif): En hızlı, riskli ama sonuç odaklı yol.
        2. Senaryo B (Sakin/Konservatif): En güvenli, test odaklı ve hata toleransı yüksek yol.
        3. Diyalektik Sentez: A ve B senaryolarındaki çelişkileri ve avantajları analiz ederek, 
           en dengeli (Sovereign) uygulama planını (DAG) oluştur.
        
        Yanıtı SADECE JSON formatında ver:
        {{
            "dialectics": {{
                "scenario_a": "Agresif planın mantığı ve riskleri",
                "scenario_b": "Konservatif planın mantığı ve güvenlik önlemleri",
                "synthesis_reasoning": "Neden bu sentez planın en optimal olduğu (Türkçe)"
            }},
            "plan": [
                {{
                    "step_id": "step_0",
                    "agent_id": "ajan_id",
                    "prompt": "Sentez planın Türkçe talimatları...",
                    "is_complex": true,
                    "dependencies": []
                }},
                {{
                    "step_id": "step_1",
                    "agent_id": "başka_ajan_id",
                    "prompt": "Önceki adımlardan gelen verilerle yapılacaklar...",
                    "is_complex": false,
                    "dependencies": ["step_0"]
                }}
            ]
        }}
        
        Kural: Eğer bir adım 3'ten fazla alt-işlem gerektiriyorsa (örn: tam bir veritabanı kurulumu veya auth api yazımı), 
        "is_complex": true değeri ver.
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role=lead_agent_role,
                prompt=prompt,
                system_prompt="Sen bir Sovereign AGI Mimarı ve Stratejistisin. Karmaşık problemleri hiyerarşik ve mantıksal katmanlara bölerken kusursuzsun."
            )
            
            data = self._parse_json(response.content)
            if not data or "plan" not in data:
                _log.warning("[AGI-DECOMPOSER] Plan ayrıştırılamadı. Boş plan dönülüyor.")
                return []

            subtasks: List[SubTask] = []
            step_id_map: Dict[str, str] = {} # step_id -> SubTask.id internal mapping

            for i, step in enumerate(data["plan"]):
                step_id = step.get("step_id", f"step_{i}")
                st_id = str(uuid.uuid4())[:12] # AGI-Standard UUID
                step_id_map[step_id] = st_id

                st = SubTask(
                    id=st_id,
                    agent_id=step.get("agent_id", "architect"),
                    prompt=step.get("prompt", ""),
                    status=TaskStatus.PENDING
                )
                
                # Faz 51: Karmaşıklık Etiketi
                st.is_complex = step.get("is_complex", False)
                
                # Bağımlılıkları çöz
                raw_deps = step.get("dependencies", [])
                st.dependencies = [step_id_map[d] for d in raw_deps if d in step_id_map]
                
                subtasks.append(st)

            _log.info(f"[AGI-DECOMPOSER] Dinamik plan oluşturuldu. Adım sayısı: {len(subtasks)}")
            return subtasks

        except Exception as e:
            _log.error(f"[AGI-DECOMPOSER] Dekompozisyon hatası: {e}")
            return []

    def _get_environment_sweep(self, context: str) -> str:
        """
        [Faz 50] Heurististik Çevre Taraması: Hedefle ilgili olabilecek dosyaları bulur.
        """
        try:
            # 1. Kök dizin listesi (shallow)
            root_files = os.listdir(".")
            
            # 2. Heuristik: Eğer hedefte 'core', 'api', 'db' gibi kelimeler geçiyorsa derinleş
            keywords = ["core", "api", "db", "tests", "llm", "auth"]
            found_paths = []
            for kw in keywords:
                if kw.lower() in context.lower():
                    # Sadece 1 seviye derinleş (Hız için)
                    if os.path.isdir(kw):
                        files = os.listdir(kw)[:10] # Sadece ilk 10 döküman
                        found_paths.append(f"{kw}/: {', '.join(files)}")
            
            snapshot = "ROOT: " + ", ".join(root_files[:20]) + "\n"
            if found_paths:
                snapshot += "DETECTED PATHS: \n" + "\n".join(found_paths)
            return snapshot
        except Exception as e:
            return f"Environment Sweep Hata: {str(e)}"

    def _parse_json(self, text: str) -> Optional[Dict]:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        return None

# Singleton
agi_goal_decomposer = GoalDecomposer()
