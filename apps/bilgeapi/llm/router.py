import os
import logging
from typing import List, Dict, Any, Optional

from apps.bilgeapi.llm.base import BaseLLMProvider, LLMResult
from apps.bilgeapi.llm.ollama_provider import OllamaProvider, MockLLMProvider

logger = logging.getLogger("bilgeapi.llm.router")

class LLMRouter(BaseLLMProvider):
    def __init__(self, provider_type: Optional[str] = None):
        self.provider_type = provider_type or os.getenv("BILGEAPI_LLM_PROVIDER", "ollama").lower()
        
        if self.provider_type == "mock":
            self.provider = MockLLMProvider()
        else:
            self.provider = OllamaProvider()
            
        logger.info(f"LLMRouter initialized with provider type: {self.provider_type}")

    def get_model_for_task(self, complexity: str) -> str:
        """
        Constraint 12: Selects models based on task complexity:
        - 'low': gemma3:4b
        - 'medium': mistral:7b
        - 'high': llama3.1:8b
        """
        comp = complexity.lower().strip()
        if comp == "low":
            return os.getenv("BILGEAPI_OLLAMA_LOW_HARDWARE_MODEL", "gemma3:4b")
        elif comp == "medium":
            return os.getenv("BILGEAPI_OLLAMA_FALLBACK_MODEL", "mistral:7b")
        else:
            # Default to high complexity model
            return os.getenv("BILGEAPI_OLLAMA_DEFAULT_MODEL", "llama3.1:8b")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        db_session: Optional[Any] = None
    ) -> LLMResult:
        """
        Routes the generate request to the active provider.
        """
        # Resolve complexity from options if available, e.g. complexity='low'
        resolved_model = model
        if not resolved_model and options and "complexity" in options:
            resolved_model = self.get_model_for_task(options["complexity"])

        return await self.provider.generate(
            prompt=prompt,
            model=resolved_model,
            options=options,
            db_session=db_session
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        db_session: Optional[Any] = None
    ) -> LLMResult:
        """
        Routes the chat request to the active provider.
        """
        resolved_model = model
        if not resolved_model and options and "complexity" in options:
            resolved_model = self.get_model_for_task(options["complexity"])

        return await self.provider.chat(
            messages=messages,
            model=resolved_model,
            options=options,
            db_session=db_session
        )
