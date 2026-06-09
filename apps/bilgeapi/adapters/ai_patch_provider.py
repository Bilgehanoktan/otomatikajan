from typing import Any, Dict


class BaseAIPatchProvider:
    provider_name = "base"

    async def generate_patch_suggestion(self, context: Dict[str, Any]) -> Dict[str, str]:
        raise NotImplementedError


class MockAIPatchProvider(BaseAIPatchProvider):
    provider_name = "mock"

    async def generate_patch_suggestion(self, context: Dict[str, Any]) -> Dict[str, str]:
        instruction = str(context.get("instruction") or "").lower()
        if "auth" in instruction:
            patch = (
                "diff --git a/apps/bilgeapi/auth.py b/apps/bilgeapi/auth.py\n"
                "--- a/apps/bilgeapi/auth.py\n"
                "+++ b/apps/bilgeapi/auth.py\n"
                "@@ -1,1 +1,2 @@\n"
                "+# AI suggestion narrows auth handling\n"
                "diff --git a/tests/unit/bilgeapi/test_auth_ai_suggestion.py b/tests/unit/bilgeapi/test_auth_ai_suggestion.py\n"
                "--- a/tests/unit/bilgeapi/test_auth_ai_suggestion.py\n"
                "+++ b/tests/unit/bilgeapi/test_auth_ai_suggestion.py\n"
                "@@ -0,0 +1,2 @@\n"
                "+def test_auth_ai_suggestion_scope():\n"
                "+    assert True\n"
            )
            return {
                "suggested_patch_code": patch,
                "rationale": "Mock suggestion touches auth.py and adds a focused test.",
                "risk_notes": "High Risk Review Required: auth.py is a sensitive file.",
            }

        patch = (
            "diff --git a/apps/bilgeapi/services/runtime.py b/apps/bilgeapi/services/runtime.py\n"
            "--- a/apps/bilgeapi/services/runtime.py\n"
            "+++ b/apps/bilgeapi/services/runtime.py\n"
            "@@ -1,1 +1,2 @@\n"
            "+# AI suggestion keeps runtime change narrowly scoped\n"
            "diff --git a/tests/unit/bilgeapi/test_runtime_ai_suggestion.py b/tests/unit/bilgeapi/test_runtime_ai_suggestion.py\n"
            "--- a/tests/unit/bilgeapi/test_runtime_ai_suggestion.py\n"
            "+++ b/tests/unit/bilgeapi/test_runtime_ai_suggestion.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+def test_runtime_ai_suggestion_scope():\n"
            "+    assert True\n"
        )
        return {
            "suggested_patch_code": patch,
            "rationale": "Mock suggestion narrows the patch and adds a focused test.",
            "risk_notes": "No sensitive files detected by the mock provider.",
        }


class OpenAIPatchProvider(BaseAIPatchProvider):
    provider_name = "openai"

    def __init__(self, *, api_key: str, model_name: str, allow_real: bool):
        self.api_key = api_key
        self.model_name = model_name
        self.allow_real = allow_real

    async def generate_patch_suggestion(self, context: Dict[str, Any]) -> Dict[str, str]:
        if not self.allow_real:
            raise RuntimeError("Real AI patch provider is disabled")
        raise RuntimeError("OpenAI patch provider is not enabled in this offline build")


class LocalAIPatchProvider(BaseAIPatchProvider):
    provider_name = "local"

    def __init__(self, *, model_name: str, allow_real: bool):
        self.model_name = model_name
        self.allow_real = allow_real

    async def generate_patch_suggestion(self, context: Dict[str, Any]) -> Dict[str, str]:
        if not self.allow_real:
            raise RuntimeError("Real AI patch provider is disabled")
        raise RuntimeError("Local AI patch provider is not configured")
