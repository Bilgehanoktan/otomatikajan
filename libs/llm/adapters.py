# ⚠️ NOT: Bu dosya (BaseProviderAdapter / GeminiAdapter) şu an aktif kullanımda değil.
# Gerçek LLM çağrıları llm/model_orchestrator.py üzerinden yapılıyor.
# İleride refactor: model_orchestrator bu adapter'ları kullanacak şekilde yeniden yazılabilir.
# GeminiAdapter.generate() içindeki mock yanıt gerçek entegrasyonla değiştirilmeli.

from abc import ABC, abstractmethod
from pydantic import BaseModel
import time
from .exceptions import LLMError, RateLimitError, EmptyResponseError

class LLMResponse(BaseModel):
    content: str
    input_tokens: int
    output_tokens: int
    model_name: str
    provider: str
    latency_s: float
    cost_usd: float

class BaseProviderAdapter(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        pass
        
    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        pass

class GeminiAdapter(BaseProviderAdapter):
    """Google Gemini için özel Adapter."""
    
    # Gerçek token fiyatları (Örnek: 1M token başına)
    PRICING = {
        "gemini-1.5-flash": {"input": 0.35, "output": 1.05},
        "gemini-1.5-pro": {"input": 3.50, "output": 10.50}
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        # import google.generativeai as genai vs.

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        rates = self.PRICING.get(model, self.PRICING["gemini-1.5-flash"])
        return (input_tokens / 1_000_000) * rates["input"] + (output_tokens / 1_000_000) * rates["output"]

    async def generate(self, prompt: str, system_prompt: str, model_name: str = "gemini-1.5-flash") -> LLMResponse:
        start_time = time.time()
        
        try:
            # Burada gerçek API çağrısı yapılır
            # response = await self.client.generate_content(...)
            
            # Mock Yanıt (Gerçek entegrasyonda API'den alınacak)
            raw_content = "LLM'den dönen yanıt"
            in_tokens = 150 # response.usage_metadata.prompt_token_count
            out_tokens = 450 # response.usage_metadata.candidates_token_count
            
            if not raw_content or raw_content.strip() == "":
                raise EmptyResponseError("Gemini boş yanıt döndü.")
                
            latency = time.time() - start_time
            cost = self.calculate_cost(in_tokens, out_tokens, model_name)
            
            return LLMResponse(
                content=raw_content,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                model_name=model_name,
                provider="gemini",
                latency_s=latency,
                cost_usd=cost
            )
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                raise RateLimitError(f"Gemini Rate Limit: {e}")
            raise LLMError(f"Gemini API Hatası: {e}")