import asyncio
import os
import sys
from unittest.mock import patch

# Proje kök dizinini path'e ekle
sys.path.append(os.path.abspath("."))

from llm.model_orchestrator import ModelOrchestrator

async def test_placeholder_detection():
    print("--- LLM Placeholder Tespiti Testi ---")
    
    # Mock environment with placeholder keys
    mock_env = {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GEMINI_API_KEY": "AI...",
        "GROQ_API_KEY": ""
    }
    
    with patch.dict(os.environ, mock_env):
        orch = ModelOrchestrator()
        
        # system_controller rolü için test et
        # preferred_providers: ["openai", "groq", "anthropic", "gemini"]
        
        try:
            print("complete_task çağrılıyor (placeholder keyler varken)...")
            await orch.complete_task(
                agent_role="system_controller",
                prompt="Test prompt",
                system_prompt="Test system prompt",
                task_id="test-task"
            )
        except RuntimeError as e:
            print(f"Beklenen Hata Yakalandi: {e}")
            if "Atlanan Placeholder" in str(e):
                print("TEST BASARILI: Placeholder anahtarlar tespit edildi ve raporlandi.")
            else:
                print("TEST BASARISIZ: Hata mesaji beklenen formatta degil.")
        except Exception as e:
            print(f"TEST BASARISIZ: Beklenmeyen hata: {type(e).__name__}: {e}")
        else:
            print("TEST BASARISIZ: Hata firlatilmadi (placeholder anahtarlara ragmen!)")

if __name__ == "__main__":
    asyncio.run(test_placeholder_detection())
