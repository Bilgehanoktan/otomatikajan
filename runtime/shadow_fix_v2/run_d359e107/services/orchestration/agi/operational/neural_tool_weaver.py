import os
import json
import uuid
from typing import Optional, List, Dict, Any
from services.orchestration.agi.schemas import ActionRecord
from libs.llm.model_orchestrator import ModelOrchestrator
from services.orchestration.application.sandbox_runner import get_sandbox_runner
from services.orchestration.agi.monitoring.nervous_system import nervous_system
from services.observability.logging import get_logger

_log = get_logger("agi_neural_tool_weaver")

class ToolRegistry:
    """Otonom üretilen araçların kaydı ve metaverisi."""
    def __init__(self, storage_path: str = "tools/autonomous/registry.json"):
        self.storage_path = storage_path
        self.tools = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def register(self, name: str, path: str, doc: str, schema: Dict):
        self.tools[name] = {
            "path": path,
            "documentation": doc,
            "input_schema": schema,
            "created_at": str(os.path.getmtime(path))
        }
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.tools, f, indent=2)

    def get_tool(self, name: str) -> Optional[Dict]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict]:
        return [{"name": k, **v} for k, v in self.tools.items()]

class NeuralToolWeaver:
    """
    Operational Core (Katman 5): Neural Tool Weaver (Sinirsel Araç Örücü).
    Yetersiz yetkinlik durumunda yeni araçlar (scriptler) yazar ve test eder.
    Sistemin dinamik yetenek havuzunu genişletir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.registry = ToolRegistry()
        self.sandbox = get_sandbox_runner()

    async def weave_capability(self, requirement: str, tool_name: Optional[str] = None, max_attempts: int = 3) -> Dict[str, Any]:
        """Yeni bir araç sentezler ve hata durumunda kendi kendini düzeltir."""
        if not tool_name:
            tool_name = f"auto_tool_{uuid.uuid4().hex[:6]}"
        
        _log.info(f"Sinirsel Yetenek Sentezleniyor: {tool_name} (Gereksinim: {requirement})")
        
        current_attempt = 1
        last_error = ""
        code = ""
        doc_block = ""

        while current_attempt <= max_attempts:
            _log.info(f"Sentez Denemesi {current_attempt}/{max_attempts}")
            
            if current_attempt == 1:
                prompt = self._build_synthesis_prompt(requirement)
            else:
                prompt = self._build_refinement_prompt(requirement, code, last_error)

            try:
                response = await self.model_orch.complete_task(
                    agent_role="developer",
                    prompt=prompt,
                    system_prompt="Sen bir AGI Neural Tool Weaver (Sinirsel Araç Örücü) bileşenisin. Görevin, sistemin yeni yetenekler kazanması için güvenli ve sağlam Python scriptleri yazmaktır."
                )
                
                code = self._extract_section(response.content, "CODE")
                doc_block = self._extract_section(response.content, "DOC")
                
                # Geçici kaydet ve test et (tools/autonomous dizini mevcut olmalı)
                path = f"tools/autonomous/{tool_name}.py"
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)

                test_res = await self._self_test(tool_name, code)
                
                if test_res["success"]:
                    self.registry.register(tool_name, path, doc_block, {"dynamic": True, "attempts": current_attempt})
                    _log.info(f"ARAÇ SENTEZLENDİ VE TEST EDİLDİ (Başarı): {tool_name}")
                    nervous_system.log_cognitive_event("tool_synthesis", True, f"Tool: {tool_name} (Attempts: {current_attempt})")
                    return {"status": "success", "tool_name": tool_name, "path": path, "attempts": current_attempt}
                else:
                    last_error = test_res["error"]
                    _log.warning(f"Sentez denemesi {current_attempt} başarısız: {last_error}")
                    nervous_system.log_cognitive_event("tool_correction", False, f"Attempt {current_attempt} failed: {last_error}")
                    current_attempt += 1

            except Exception as e:
                _log.error(f"Tool weaving (attempt {current_attempt}) hatası: {e}")
                last_error = str(e)
                current_attempt += 1

        return {"status": "failed", "reason": f"Max attempts reached. Last error: {last_error}"}

    def _build_synthesis_prompt(self, requirement: str) -> str:
        return f"""
        Şu gereksinimi karşılayan bir Python scripti yaz: {requirement}
        
        Kurallar:
        1. Script tek başına çalışabilir olmalı.
        2. 'main(params: dict) -> dict' fonksiyonuna sahip olmalı.
        3. Dış bağımlılık kullanmamaya çalış (standard library tercih et).
        4. Hataları handle et ve anlamlı hata mesajları döndür.
        
        Yanıtı şu formatta ver:
        ---CODESTART---
        [PYTHON KODU]
        ---CODEEND---
        ---DOCSTART---
        Aracın ne işe yaradığı ve girdi parametre şeması (JSON)
        ---DOCEND---
        """

    def _build_refinement_prompt(self, requirement: str, code: str, error: str) -> str:
        return f"""
        Önceki yazdığın script şu hatayı verdi: {error}
        
        Gereksinim: {requirement}
        Mevcut Kod:
        {code}
        
        Lütfen bu hatayı düzelt ve scripti tekrar yaz. SADECE kodu ve dokümantasyonu güncelle.
        
        Format:
        ---CODESTART---
        [DÜZELTİLMİŞ KOD]
        ---CODEEND---
        ---DOCSTART---
        [GÜNCELLENMİŞ DOKÜMANTASYON]
        ---DOCEND---
        """

    async def _self_test(self, name: str, code: str) -> Dict[str, Any]:
        """Üretilen aracın temel çalışabilirliğini sandbox'ta test eder."""
        test_wrapper = f"""
{code}
import json
try:
    # Temel bir çağırma denemesi (boş params ile)
    # Eğer script parametre istiyorsa, duck-typing veya try/except ile handle edilmeli.
    # Gelecekte burası LLM-produced 'test_cases' ile zenginleştirilecek.
    result = main({{}})
    print("---TEST_SUCCESS---")
    print(json.dumps({{"result": result}}))
except Exception as e:
    print("---TEST_FAILURE---")
    print(str(e))
    import sys
    sys.exit(1)
"""
        res = await self.sandbox.run_python(test_wrapper, timeout=5)
        if res.success:
            return {"success": True, "error": ""}
        else:
            return {"success": False, "error": res.stderr or res.stdout or "Unknown failure"}

    def _extract_section(self, content: str, tag: str) -> str:
        import re
        pattern = f"---{tag}START---(.*?)---{tag}END---"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

# Singleton
neural_tool_weaver = NeuralToolWeaver()
tool_registry = ToolRegistry()
