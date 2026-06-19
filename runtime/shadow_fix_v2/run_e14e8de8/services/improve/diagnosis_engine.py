import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from services.observability.logging import get_logger
from services.orchestration.indexing.system_indexer import SystemIndexer
from libs.llm.model_orchestrator import ModelOrchestrator

logger = get_logger("diagnosis_engine")

class DiagnosisEngine:
    """
    OperationalIncident verilerini analiz ederek hata kaynağını tespit eder 
    ve SelfUpdater için düzeltme talimatı üretir.
    """

    def __init__(self, model_orch: ModelOrchestrator, project_root: str):
        self.model_orch = model_orch
        self.project_root = Path(project_root).resolve()
        self.indexer = SystemIndexer(project_root=str(self.project_root))

    def _extract_stack_trace(self, payload: Dict[str, Any]) -> str:
        """Payload içindeki hata mesajı veya stack trace'i bulur."""
        for key in ["stack_trace", "error", "exception", "traceback", "message"]:
            val = payload.get(key)
            if val and isinstance(val, str):
                return val
        return str(payload)

    async def diagnose(self, incident_id: str, incident_type: str, message: str, payload: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """
        Olayı analiz eder. 
        Döner: (target_file_relative_path, fix_instruction)
        """
        evidence = self._extract_stack_trace(payload) or message
        
        logger.info(f"Diagnosing incident {incident_id} type={incident_type}...")

        # LLM based diagnosis
        prompt = f"""
SEN BİR SİSTEM TEŞHİS UZMANISIN (DIAGNOSIS ENGINE).

SİSTEMDE ŞÖYLE BİR OLAY TESPİT EDİLDİ:
OLAY TİPİ: {incident_type}
MESAJ: {message}

KANIT (STACK TRACE / PAYLOAD):
```text
{evidence}
```

GÖREVİN:
1. Bu hatanın gerçekte hangi kaynak dosyadan (.py) kaynaklandığını bul.
2. Dosya yolu mutlaka proje köküne göre RELATIVE olmalı (örn: services/api/main.py).
3. Bu hatayı düzeltmek için ne yapılması gerektiğini teknik bir dille açıkla.

ÇIKTI FORMATI (SADECE ŞU İKİ SATIRI DÖNDÜR):
TARGET_FILE: <dosya_yolu>
INSTRUCTION: <teknik_düzeltme_talimatı>
"""

        response = await self.model_orch.complete(
            messages=[{"role": "system", "content": "You are a master debugger."}, {"role": "user", "content": prompt}],
            preferred_agent="engineering-system-architect"
        )
        
        content = getattr(response, "content", str(response))
        
        target_file = None
        instruction = "Hata analizi yapılamadı."

        # Parse LLM output
        for line in content.splitlines():
            if line.startswith("TARGET_FILE:"):
                target_file = line.replace("TARGET_FILE:", "").strip()
            elif line.startswith("INSTRUCTION:"):
                instruction = line.replace("INSTRUCTION:", "").strip()

        if not target_file:
            logger.warning(f"DiagnosisEngine could not identify target file for incident {incident_id}")
            # Fallback regex search for filenames in traceback
            files_in_trace = re.findall(r"File \"(.*?)\",", evidence)
            if files_in_trace:
                # Try to find a core file (not internal libs or venv)
                for f in reversed(files_in_trace):
                    if ".venv" not in f and "site-packages" not in f and self.project_root.name in f:
                         # Normalize to relative path
                         p = Path(f)
                         try:
                             target_file = str(p.relative_to(self.project_root))
                             break
                         except:
                             pass

        return target_file, instruction
