import re
import os
from typing import List, Dict, Any, Optional
from observability.logging import get_logger

_log = get_logger("agi_metacognition")

class MetacognitiveNode:
    """
    Üst-Bilişsel Düğüm (Metacognitive Node).
    Sistemin kendi mimari bütünlüğünü (drift) ve bilişsel verimliliğini izler.
    Metacognition: Kendi düşünce süreçlerini izleme ve yönetme yeteneği.
    """
    
    ARCH_SPEC_PATH = "AGI_SISTEM_MIMARISI.md"
    REQUIRED_STRUCTURE = [
        "core/agi/cognitive",
        "core/agi/operational",
        "core/agi/learning",
        "core/agi/security"
    ]

    def check_architectural_drift(self) -> Dict[str, Any]:
        """
        Sistemin mevcut yapısını AGI_SISTEM_MIMARISI.md ve beklenen klasör yapısıyla karşılaştırır.
        """
        _log.info("[META] Mimari kayma (Drift) analizi başlatılıyor...")
        
        drift_detected = False
        missing_folders = []
        
        # 1. Klasör yapısı kontrolü
        for folder in self.REQUIRED_STRUCTURE:
            if not os.path.exists(folder):
                drift_detected = True
                missing_folders.append(folder)
                _log.error(f"[DRIFT] Kritik klasör eksik: {folder}")

        # 2. Mimari döküman kontrolü (Basit varlık kontrolü)
        if not os.path.exists(self.ARCH_SPEC_PATH):
            drift_detected = True
            _log.critical("[DRIFT] Mimari spesifikasyon dosyası (AGI_SISTEM_MIMARISI.md) KAYIP!")

        return {
            "drift_detected": drift_detected,
            "missing_components": missing_folders,
            "integrity_score": 1.0 - (len(missing_folders) * 0.2),
            "status": "UNSTABLE" if drift_detected else "STABLE"
        }

    def analyze_cognitive_trace(self, actions: List[Any]) -> Dict[str, Any]:
        """
        Eylem geçmişini inceleyerek 'Döngüsel Düşünme' (Redundant reasoning) desenlerini arar.
        """
        _log.info("[META] Bilişsel iz (Cognitive Trace) analizi yapılıyor...")
        
        redundancy_count = 0
        seen_prompts = set()
        
        for act in actions:
            # Benzer inputları saptama
            p_hash = str(act.input_data)[:50] # Basit hash
            if p_hash in seen_prompts:
                redundancy_count += 1
            seen_prompts.add(p_hash)

        efficiency_score = 1.0 - (redundancy_count * 0.1)
        
        return {
            "efficiency_score": max(0.0, efficiency_score),
            "redundancy_detected": redundancy_count > 0,
            "redundancy_count": redundancy_count
        }

# Singleton
metacognition = MetacognitiveNode()
