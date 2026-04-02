import asyncio
import os
import sys

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_llm_fix():
    print("--- [FAZ 12.1: LLM ORKESTRATÖR DOĞRULAMA] ---")
    try:
        from llm.model_orchestrator import ModelOrchestrator
        orch = ModelOrchestrator()
        
        test_messages = [
            {"role": "system", "content": "Sen egemen bir AGI asistanısın. Kısa ve teknik cevap ver."},
            {"role": "user", "content": "Sovereign AGI nedir? Tek kelimeyle cevap ver."}
        ]
        
        print("Model çağrısı yapılıyor...")
        response = await orch.complete(test_messages)
        print(f"Alınan Yanıt: '{response}'")
        
        if response and len(response) > 0:
            print("[BAŞARILI] LLM orkestratör girinti hatası giderildi ve iletişim sağlandı.")
        else:
            print("[BAŞARISIZ] Boş yanıt alındı.")
            
    except Exception as e:
        print(f"[BAŞARISIZ] Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_fix())
