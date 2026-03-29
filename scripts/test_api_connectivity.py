
import asyncio
import os
import sys

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

async def test_providers():
    from llm.model_orchestrator import ModelOrchestrator
    orchestrator = ModelOrchestrator()
    
    providers_to_test = ["openai", "gemini", "groq", "openrouter", "moonshot", "deepseek", "anthropic"]
    
    results = {}
    
    print("--- API Connectivity Test ---")
    for provider in providers_to_test:
        print(f"Testing {provider}...")
        try:
            # Basit bir "Merhaba" testi
            response = await orchestrator.complete(
                messages=[{"role": "user", "content": "Hi, just reply with 'OK'"}],
                force_provider=provider
            )
            print(f"  [SUCCESS] {provider}: {response.strip()}")
            results[provider] = "Success"
        except Exception as e:
            print(f"  [FAILURE] {provider}: {str(e)[:100]}...")
            results[provider] = f"Failure: {str(e)[:50]}"
            
    print("\n--- Summary ---")
    for p, res in results.items():
        print(f"{p}: {res}")

if __name__ == "__main__":
    asyncio.run(test_providers())
