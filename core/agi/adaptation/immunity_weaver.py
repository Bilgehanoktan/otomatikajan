import os
from typing import List, Dict, Any, Optional
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_immunity_weaver")

class ImmunityWeaver:
    """
    Adaptation Core (Katman 19): Immunity Weaver.
    Tespit edilen patojenlere karşı otonom 'Antikor' (savunmacı kod) üretir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None, immunity_root: str = "core/agi/immunity"):
        self.model_orch = model_orch or ModelOrchestrator()
        self.immunity_root = immunity_root

    async def weave_antibodies(self, pathogens: List[Dict[str, Any]]) -> List[str]:
        """
        Patojenlere karşı otonom antikorlar (Python dekoratörleri) üretir.
        """
        if not pathogens:
            return []
            
        _log.info(f"Antikor Sentezi (Antibody Weaving) başlatılıyor... Patojen Sayısı: {len(pathogens)}")
        
        created_antibodies = []
        os.makedirs(self.immunity_root, exist_ok=True)
        init_file = os.path.join(self.immunity_root, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "w").close()

        for p in pathogens:
            antibody_code = await self._synthesize_antibody(p)
            if antibody_code:
                # Modül bazlı antikor dosyası oluştur
                antibody_name = f"antibody_{p.get('id', 'global')}.py"
                with open(os.path.join(self.immunity_root, antibody_name), "w", encoding="utf-8") as f:
                    f.write(antibody_code)
                created_antibodies.append(antibody_name)
                _log.info(f"Antikor Üretildi: {antibody_name}")
                
        return created_antibodies

    async def _synthesize_antibody(self, pathogen: Dict[str, Any]) -> Optional[str]:
        """LLM kullanarak savunmacı Python kodu üretir."""
        prompt = f"""
        Patojen (Error Pattern):
        {json.dumps(pathogen, indent=2)}
        
        Bu hataya karşı bir 'Sarma' (Wrapper) veya 'Dekoratör' (Decorator) antikor yaz. 
        Bu antikor, hedef fonksiyonu sarmalı ve aynı hatanın (Pathogen) oluşmasını engellemeli veya yönetmeli.
        Hata oluşursa 'immuno_soft_fallback' yapmalı ve loglamalı.
        
        Örn:
        def antibody_retry_on_timeout(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                ...
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI İmmunoloğusun. Hatalara karşı dayanıklı (Robust) Python antikorları yazarsın."
            )
            return response.content
        except Exception as e:
            _log.error(f"Antibody synthesis failed: {e}")
            return None

import json
# Singleton
immunity_weaver = ImmunityWeaver()
