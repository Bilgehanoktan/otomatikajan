import json
import uuid
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger
from services.orchestration.agi.task_governance import GovernedTask, GovernanceStatus

_log = get_logger("agi_recursive_decomposer")

class RecursiveDecomposer:
    """
    Sovereign AGI (Faz 51): Rekürsif Stratejik Dekompozisyon.
    Karmaşık hedefleri analiz eder, en uygun uzman ajanları seçer ve 
    görevleri mantıksal bir bağımlılık ağacına (DAG) dönüştürür.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def decompose_goal(self, title: str, description: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Üst-Hedef düzeyinde analiz yapar ve bir görev ağacı döndürür.
        """
        _log.info(f"[DECOMPOSER] Hedef dekompoze ediliyor: {title}")
        
        prompt = f"""
SİSTEMİK STRATEJİ VE GÖREV DEKOMPOZİSYONU (Faz 51: Sovereign Depth)
-------------------------------------------------------------------
HEDEF BAŞLIĞI: {title}
HEDEF AÇIKLAMASI: {description}
MEVCUT BAĞLAM: {json.dumps(context or {}, indent=2)}

GÖREV: Bu üst-hedefe ulaşmak için gereken teknik ve operasyonel adımları belirle. 
Sistemi bir "Yığın" (Stack) olarak değil, bir "Bağımlılık Ağacı" (DAG) olarak kurgula.

KURALLAR:
1. SADECE gerekli uzmanlıkları (architect, backend_dev, frontend_dev, qa_engineer, devops, security, data_eng, tech_writer) seç.
2. Görevler arası 'dependencies' (bağımlılık) ilişkilerini kesin olarak belirle (Örn: 'backend_dev' görevi 'architect' bitmeden başlayamaz).
3. Her görev için 'inhibition' (ketleme) ekle: Ajana neyi YAPMAMASI gerektiğini söyle.
4. Her görev için 'acceptance_criteria' (kabul kriterleri) ekle.

JSON FORMATINDA YANIT VER:
{{
  "strategic_reasoning": "Neden bu yolu seçtiğinin analizi...",
  "tasks": [
    {{
      "task_id": "T1",
      "agent_id": "architect",
      "objective": "Görevin teknik amacı...",
      "inhibition": "Sadece mimari sınırları çiz, kod yazma.",
      "dependencies": [],
      "acceptance_criteria": ["Log tasarımı tamam mı?", "DB şeması hazır mı?"]
    }},
    {{
      "task_id": "T2",
      "agent_id": "backend_dev",
      "objective": "...",
      "inhibition": "...",
      "dependencies": ["T1"],
      "acceptance_criteria": [...]
    }}
  ]
}}
"""

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen Egemen AGI Baş Stratejistisin. Karmaşık projeleri kusursuz birer teknik DAG'a dönüştürürsün."
            )
            
            # JSON temizleme ve yükleme
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if not match:
                raise ValueError("LLM response did not contain a valid JSON object.")
            
            plan_data = json.loads(match.group())
            _log.info(f"[DECOMPOSER] Stratejik plan oluşturuldu: {len(plan_data.get('tasks', []))} görev.")
            return plan_data.get("tasks", [])
            
        except Exception as e:
            _log.error(f"[DECOMPOSER] Dekompozisyon hatası: {e}")
            # Fallback: Basit tek ajanlı plan (Guvenlik mekanizması)
            return [{
                "task_id": "T1",
                "agent_id": "architect",
                "objective": f"Fallback Plan: {title}",
                "inhibition": "Dekompozisyon başarısız oldu, manuel ilerle.",
                "dependencies": [],
                "acceptance_criteria": ["İşlev doğrulandı mı?"]
            }]
