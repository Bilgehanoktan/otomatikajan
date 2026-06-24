from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMResult:
    def __init__(
        self,
        text: str,
        model: str,
        fallback_used: bool,
        latency: float,
        usage: Optional[Dict[str, Any]] = None
    ):
        self.text = text                  # Redacted response text
        self.model = model                # Selected model name
        self.fallback_used = fallback_used
        self.latency = latency
        self.usage = usage or {}          # Token/Usage info

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "fallback_used": self.fallback_used,
            "latency": self.latency,
            "usage": self.usage
        }

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        db_session: Optional[Any] = None
    ) -> LLMResult:
        """
        Generates text for a given prompt, with fallback logic.
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        db_session: Optional[Any] = None
    ) -> LLMResult:
        """
        Generates a chat completion, with fallback logic.
        """
        pass
