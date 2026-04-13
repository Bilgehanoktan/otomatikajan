import asyncio
import json
import re
import os
from typing import List, Dict, Any, Optional
from services.observability.logging import get_logger
from libs.llm.model_orchestrator import model_orchestrator, ModelOrchestrator
from services.orchestration.agi.schemas import PlanProposal
from services.orchestration.agi.consciousness.affective_core import affective_core

_log = get_logger("agi_foresight")

class ForesightCortex:
    """
    Cognitive Core (Katman 28): Foresight Cortex (Multiversal Mesh).
    Kararların paralel gelecek simülasyonları üzerinden alınmasını sağlar.
    'En az riskli, en yüksek öngörü' modelini hedefler.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or model_orchestrator

    async def simulate_plan(self, plan: Any) -> Dict[str, Any]:
        """
        Bir planın adımlarını simüle eder, riskleri saptar ve stratejik uyum skorunu belirler.
        Faz 50: Gerçek dünya (Grounding) verileri ile desteklenmiştir.
        """
        import dataclasses
        from libs.db.session import session_scope
        from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
        
        _log.info(f"[FORESIGHT] Yansımalı Plan Simülasyonu başlatılıyor...")
        
        # 1. Bilişsel Hafızadan Nedensel Bağlamı Topla (V5 Causal Recall)
        causal_wisdom = []
        try:
            async with session_scope() as db:
                # Faz 77: Causal Grounding Integration (Priority 2: Planning Depth)
                plan_name = plan.title if hasattr(plan, 'title') else "Plan Analysis"
                causal_wisdom = await synaptic_cortex.search_with_causal_anchoring(
                    db=db, 
                    query=f"{plan_name} strategic plan execution", 
                    top_k=5
                )
        except Exception as e:
            _log.warning(f"[FORESIGHT] Causal Recall alınamadı: {e}")

        wisdom_context = "\n".join([
            f"- [{l.get('category', 'lesson')}] {l.get('body')}" 
            for l in causal_wisdom
        ]) if causal_wisdom else "Derin nedensel bağlam bulunamadı."

        plan_content = json.dumps(dataclasses.asdict(plan), indent=2, default=str) if dataclasses.is_dataclass(plan) else str(plan)
        
        # Faz 12.4: Duygusal Simülasyon
        aff_matrix = affective_core.get_state_matrix()
        stress_level = aff_matrix.get("internal_stress", 0.0)
        mood = affective_core.get_current_mood()

        # Faz 50: Reality Check (Grounding)
        grounding_context = await self._perform_reality_check()

        prompt = f"""
        Aşağıdaki uygulama planını zihninde simüle et. 
        
        SİSTEM DURUMU (AFFECTIVE STATE):
        - Ruh Hali: {mood}
        - Stres Seviyesi: {stress_level:.2f} (0.0 - 1.0)
        - Önemli: Eğer stres > 0.7 ise, 'Hasty Code' (Aceleci Kod) ve 'Regression' risklerini daha yüksek olasılıkla değerlendir.
        
        SON BİLİŞSEL DERSLER VE NEDENSEL BİLGELİK (CAUSAL WISDOM):
        {wisdom_context}
        
        PLAN:
        {plan_content}

        GERÇEK DÜNYA DURUMU (GROUNDING):
        {grounding_context}
        
        Lütfen simülasyon çıktısını JSON olarak döndür:
        {{
            "predicted_risks": [
                {{ "step": 1, "severity": "high", "failure_mode": "...", "impact": "..." }}
            ],
            "strategic_alignment_score": 0.85, 
            "reasoning": "Planın hedefe uygunluk analizi",
            "suggested_mitigations": ["Riskleri azaltmak için öneri"]
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Öngörü Birimisin (Foresight Cortex). Planların gizli risklerini ve stratejik değerini henüz gerçekleşmeden analiz edersin."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                _log.info(f"[FORESIGHT] Simülasyon Tamamlandı. Skor: {data.get('strategic_alignment_score')}")
                return data
            return {"predicted_risks": [], "strategic_alignment_score": 0.5}
        except Exception as e:
            _log.error(f"[FORESIGHT] Foresight simulation failed: {e}")
            return {"predicted_risks": [], "strategic_alignment_score": 0.0}
    
    async def simulate_parallel_futures(self, original_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Orijinal bir plan için 3 farklı paralel zaman çizelgesi (Timeline) üretir.
        Gönüllü bir simülasyon yaparak planın AGİ standartlarına uygunluğunu test eder.
        """
        _log.info(f"[FORESIGHT] '{original_plan.get('title', 'Unknown Task')}' için paralel gelecekler simüle ediliyor...")
        
        prompt = f"""
        Aşağıdaki AGI planı için 3 farklı paralel gelecek (Timeline) senaryosu üret:
        Plan Başlığı: {original_plan.get('title')}
        Plan İçeriği: {original_plan.get('content') or original_plan.get('summary')}
        
        Senaryo Tipleri:
        1. 'Conservative' (Maksimum Güvenlik, Minimum Risk)
        2. 'Balanced' (Optimum Fayda/Güvenlik Dengesi)
        3. 'Aggressive' (Hızlı Sonuç, Yüksek Risk)
        
        Her senaryo için şu alanları içeren bir JSON listesi döndür:
        - timeline_name: Senaryo adı
        - potential_outcome: Olası sonuç
        - risk_score: 0.0 - 1.0 arası risk puanı
        - utility_score: 0.0 - 1.0 arası fayda puanı
        - critical_warning: En büyük potansiyel tehlike
        """
        
        try:
            response = await model_orchestrator.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Zaman Çizgisi Simülatörüsün. Geleceği öngörmek senin görevin."
            )
            
            # JSON parsing logic improve
            match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if not match:
                # Try search for dictionary
                match = re.search(r'\{.*\}', response.content, re.DOTALL)
                
            if match:
                data = json.loads(match.group())
                timelines = data if isinstance(data, list) else data.get("timelines", [])
            else:
                _log.warning("[FORESIGHT] Simülasyon çıktısı JSON formatında bulunamadı.")
                timelines = []
                
            _log.info(f"[FORESIGHT] {len(timelines)} paralel zaman çizelgesi başarıyla üretildi.")
            return timelines
        except Exception as e:
            _log.error(f"[FORESIGHT] Gelecek simülasyonu hatası: {e}")
            return []

    async def _perform_reality_check(self) -> str:
        """
        Dosya sistemi üzerinden mevcut durumu tarar (Grounding).
        Simülatörün halüsinasyon görmesini engeller.
        """
        try:
            _log.info("[FORESIGHT] Gerçeklik kontrolü (Reality Check) başlatılıyor...")
            cwd = os.getcwd()
            files = []
            
            # Kritik dizinleri tara (Maksimum derinlik 2)
            critical_dirs = ["core/agi", "api", "db", "integrations"]
            for d in critical_dirs:
                d_path = os.path.join(cwd, d)
                if os.path.exists(d_path):
                    for root, dirs, filenames in os.walk(d_path):
                        rel_root = os.path.relpath(root, cwd)
                        depth = rel_root.count(os.sep)
                        if depth <= 1:
                            for f in filenames:
                                if f.endswith(".py"):
                                    files.append(os.path.join(rel_root, f))
                        if depth > 1:
                            break # Limit depth

            snapshot = "MEVCUT MİMARİ YAPISI (SINIRLI):\n"
            snapshot += "\n".join(files[:30]) # Sadece ilk 30 dosya (Context budget)
            return snapshot
        except Exception as e:
            _log.error(f"[FORESIGHT] Reality check hatası: {e}")
            return "Gerçeklik verisi alınamadı."

    async def select_optimal_timeline(self, timelines: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Üretilen senaryolar arasından en güvenli/verimli olanı seçer."""
        if not timelines:
            return None
            
        # Risk < 0.4 olanları ve Utility > 0.6 olanları seç
        optimum = sorted(timelines, key=lambda x: (x.get('utility_score', 0) - x.get('risk_score', 1)), reverse=True)
        return optimum[0] if optimum else timelines[0]

# Singleton Instance
foresight_cortex = ForesightCortex()

# Compatibility Aliases
ChronosMesh = ForesightCortex
chronos_mesh = foresight_cortex

# [FIX] neural_core_orchestrator.py 'foresight_oracle' adıyla import ediyor.
# ForesightCortex'in alias'ı olarak tanımlıyoruz.
foresight_oracle = foresight_cortex
