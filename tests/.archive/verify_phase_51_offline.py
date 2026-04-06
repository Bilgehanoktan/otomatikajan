import asyncio
import uuid
import json
from unittest.mock import patch, MagicMock
from packages.orchestration.agi.central_executive import central_executive
from packages.orchestration.agi.schemas import SourceType
from packages.llm_gateway.llm_types import LLMResponse

from packages.packages.observability.logging import get_logger

_log = get_logger("verify_phase_51_offline")

# --- MOCK DATA (YENİ DAG ŞEMASI) ---
MOCK_DECOMPOSITION_JSON = {
    "reasoning": "Planlanan DAG yapısı: DB tasarımı ve ardından rekürsif API.",
    "plan": [
        {
            "step_id": "step_0",
            "agent_id": "backend_dev",
            "prompt": "Database Schema Design: Web servisi için tabloları tasarla.",
            "dependencies": []
        },
        {
            "step_id": "step_1",
            "agent_id": "architect",
            "prompt": "Alt-plan: API ayrıntılarını oluştur.",
            "dependencies": ["step_0"],
            "is_complex": True,
            "complexity_reasoning": "API katmanı çok kapsamlı, alt-görevlere bölünmeli."
        }
    ]
}

MOCK_SUB_DECOMPOSITION_JSON = {
    "reasoning": "API alt-planı: Endpoint A uygulaması.",
    "plan": [
        {
            "step_id": "sub_step_0",
            "agent_id": "backend_dev",
            "prompt": "Implement Endpoint A: API implementasyonu detayları.",
            "dependencies": []
        }
    ]
}

async def mock_complete_task(*args, **kwargs):
    prompt = kwargs.get("prompt", "").upper()
    
    # 1. Ana Planlama (DAG Decompose)
    if "WEB SERVİSİ" in prompt and "PLAN" in prompt:
        return LLMResponse(content=json.dumps(MOCK_DECOMPOSITION_JSON), input_tokens=10, output_tokens=10, model_name="mock", provider="mock", latency_s=0.1, cost_usd=0)
    
    # 2. Alt Planlama (Recursive Decompose)
    if "ALT-PLAN" in prompt and "PLAN" in prompt:
        return LLMResponse(content=json.dumps(MOCK_SUB_DECOMPOSITION_JSON), input_tokens=10, output_tokens=10, model_name="mock", provider="mock", latency_s=0.1, cost_usd=0)
    
    # 3. Yürütme (Ajan Çıktısı)
    if "ALT-PLAN" in prompt:
        return LLMResponse(content="[SUB-PLAN RESULT]: Endpoint A implemented successfully.", input_tokens=10, output_tokens=10, model_name="mock", provider="mock", latency_s=0.1, cost_usd=0)
    
    return LLMResponse(content="[TASK OUTPUT]: Logic implemented in mock mode.", input_tokens=10, output_tokens=10, model_name="mock", provider="mock", latency_s=0.1, cost_usd=0)

async def test_recursive_decomposition_offline():
    print("\n[PHASE 51] OFFLINE BİLİŞSEL DERİNLİK DOĞRULAMA (MOCK MODE) BAŞLATILIYOR...")
    
    test_goal = "Karmaşık bir WEB SERVİSİ oluştur."
    description = "DAG ve Recursion testi için mock veriler kullanılacak."
    
    # ModelOrchestrator.complete_task metodunu yamala (429/402 engeline karşı)
    with patch("packages.llm_gateway.model_orchestrator.ModelOrchestrator.complete_task", side_effect=mock_complete_task):
        try:
            episode = await central_executive.execute_thought_cycle(
                raw_input=f"HEDEF: {test_goal}\nAÇIKLAMA: {description}",
                source=SourceType.USER_MESSAGE,
                input_id=f"test_offline_51_{str(uuid.uuid4())[:8]}"
            )
            
            print(f"\n[+] Episode Tamamlandı. Durum: {'BAŞARILI' if episode.final_output else 'BELİRSİZ'}")
            print(f"[+] Final Output Snapshot: {episode.final_output[:200]}...")
            print(f"[+] Toplam Aksiyon: {len(episode.actions)}")
            
            # Doğrulama: Final çıktısında hem normal görev hem de sub-task çıktısı olmalı
            found_main = "[TASK OUTPUT]" in episode.final_output
            found_sub = "[SUB-PLAN RESULT]" in episode.final_output
            
            if found_main and found_sub:
                print("\n[SUCCESS] DAG Yürütme ve Rekürsif Derinlik (Phase 51) KOD SEVİYESİNDE DOĞRULANDI.")
            else:
                print(f"\n[WARNING] Beklenen izler eksik. Main: {found_main}, Sub: {found_sub}")

        except Exception as e:
            print(f"[-] HATA: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_recursive_decomposition_offline())
