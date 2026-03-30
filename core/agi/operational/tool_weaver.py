import os
import json
import uuid
from typing import Optional, List, Dict, Any
from core.agi.schemas import ActionRecord
from llm.model_orchestrator import ModelOrchestrator
from core.sandbox_runner import get_sandbox_runner
from observability.logging import get_logger

_log = get_logger("agi_tool_weaver")

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
        with open(self.storage_path, "w") as f:
            json.dump(self.tools, f, indent=2)

    def get_tool(self, name: str) -> Optional[Dict]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict]:
        return [{"name": k, **v} for k, v in self.tools.items()]

class ToolWeaver:
    """
    Operational Core (Katman 5): Autonomous Tool Synthesis.
    Yetersiz yetkinlik durumunda yeni araçlar (scriptler) yazar ve test eder.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.registry = ToolRegistry()
        self.sandbox = get_sandbox_runner()

    async def weave_capability(self, requirement: str, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Yeni bir araç sentezler."""
        if not tool_name:
            tool_name = f"auto_tool_{uuid.uuid4().hex[:6]}"
        
        _log.info(f"Yetenek Sentezleniyor: {tool_name} (Gereksinim: {requirement})")

        prompt = f"""
        Şu gereksinimi karşılayan bir Python scripti yaz: {requirement}
        
        Kurallar:
        1. Script tek başına çalışabilir olmalı.
        2. 'main(params: dict) -> dict' fonksiyonuna sahip olmalı.
        3. Dış bağımlılık kullanmamaya çalış (standard library tercih et).
        4. Hataları handle et.
        
        Yanıtı şu formatta ver:
        ---CODESTART---
        [PYTHON KODU]
        ---CODEEND---
        ---DOCSTART---
        Aracın ne işe yaradığı ve girdi parametre şeması (JSON)
        ---DOCEND---
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="developer",
                prompt=prompt,
                system_prompt="Sen bir AGI Tool Weaver (Araç Örücü) bileşenisin. Görevin, sistemin yeni yetenekler kazanması için güvenli ve sağlam Python scriptleri yazmaktır."
            )
            
            code = self._extract_section(response.content, "CODE")
            doc_block = self._extract_section(response.content, "DOC")
            
            # Kaydet
            path = f"tools/autonomous/{tool_name}.py"
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)

            # Test Et
            test_ok = await self._self_test(tool_name, code)
            
            if test_ok:
                self.registry.register(tool_name, path, doc_block, {"dynamic": True})
                _log.info(f"ARAÇ SENTEZLENDİ VE TEST EDİLDİ: {tool_name}")
                return {"status": "success", "tool_name": tool_name, "path": path}
            else:
                _log.error(f"Araç testi başarısız: {tool_name}")
                return {"status": "failed", "reason": "Self-test failed"}

        except Exception as e:
            _log.error(f"Tool weaving hatası: {e}")
            return {"status": "error", "message": str(e)}

    async def _self_test(self, name: str, code: str) -> bool:
        """Üretilen aracın temel çalışabilirliğini sandbox'ta test eder."""
        test_wrapper = f"""
        {code}
        try:
            # Temel bir çağırma denemesi
            result = main({{}})
            print(f"SUCCESS: {{result}}")
        except Exception as e:
            print(f"FAILURE: {{e}}")
            exit(1)
        """
        res = await self.sandbox.run_python(test_wrapper, timeout=5)
        return res.success

    def _extract_section(self, content: str, tag: str) -> str:
        import re
        pattern = f"---{tag}START---(.*?)---{tag}END---"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

# Singleton
tool_weaver = ToolWeaver()
tool_registry = ToolRegistry()
