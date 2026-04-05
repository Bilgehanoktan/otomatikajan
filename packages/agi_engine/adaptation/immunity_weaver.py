import ast
import re
import json
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
                cleaned = self._sanitize_python_output(antibody_code)
                final_code = self._ensure_imports(cleaned)
                if self._validate_python_output(final_code):
                    # Modül bazlı antikor dosyası oluştur
                    antibody_name = f"antibody_{p.get('id', 'global')}.py"
                    with open(os.path.join(self.immunity_root, antibody_name), "w", encoding="utf-8") as f:
                        f.write(final_code)
                    created_antibodies.append(antibody_name)
                    _log.info(f"Antikor Üretildi (Doğrulandı): {antibody_name}")
                else:
                    _log.warning(f"Patojen {p.get('id')} için geçersiz Python kodu üretildi, kaydedilmedi.")
                
        return created_antibodies

    def _sanitize_python_output(self, raw: str) -> str:
        """Markdown fence'lerini temizler ve yan metinleri ayıklar."""
        text = raw.strip()
        
        # 1. Kod bloklarını regex ile yakala (En güvenli yöntem)
        # re.DOTALL ile satır sonlarını da kapsar
        pattern = r"```(?:python)?\s*([\s\S]*?)```"
        matches = re.findall(pattern, text)
        if matches:
            # En uzun bloğu veya ilkini al
            text = max(matches, key=len).strip()
        
        # 2. Gereksiz başlıkları (Sure!, Here is etc.) temizle
        lines = text.split("\n")
        while lines and not self._is_valid_python_line(lines[0]):
            lines.pop(0)
            
        return "\n".join(lines).strip()

    def _is_valid_python_line(self, line: str) -> bool:
        """Bir satırın geçerli bir Python başlangıcı olup olmadığını kontrol eder."""
        line = line.strip()
        if not line or line.startswith(("#", '"""', "'''")): 
            return True
        # Temel anahtar kelimeler
        if any(line.startswith(kw) for kw in ["def ", "class ", "import ", "from ", "@", "async "]):
            return True
        # Basit atamalar
        if "=" in line and re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*=", line):
            return True
        return False

    def _ensure_imports(self, code: str) -> str:
        """Eksik importları koda enjekte eder (Faz 12.1 Stabilization)."""
        needed = []
        if "functools." in code and "import functools" not in code:
            needed.append("import functools")
        if "asyncio." in code and "import asyncio" not in code:
            needed.append("import asyncio")
        if "json." in code and "import json" not in code:
            needed.append("import json")
        if "logging." in code and "import logging" not in code:
            needed.append("import logging")
            
        if needed:
            return "\n".join(needed) + "\n\n" + code
        return code

    def _validate_python_output(self, code: str) -> bool:
        """ast.parse ile kodun geçerli olup olmadığını kontrol eder."""
        if not code:
            return False
        try:
            ast.parse(code)
            return True
        except SyntaxError as se:
            _log.warning(f"Sentezlenen kod gecersiz (SyntaxError): {se}")
            return False

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

# Singleton
immunity_weaver = ImmunityWeaver()
