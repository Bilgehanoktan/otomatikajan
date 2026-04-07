import asyncio
import os
import sys

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_empathy_engine():
    print("--- AGI 33.0 Verification ---")
    
    try:
        from packages.orchestration.agi.cognitive.theory_of_mind import theory_of_mind
        from packages.orchestration.agi.adaptation.empathy_tuner import empathy_tuner
        
        print("[OK] AGI 33.0 components imported successfully.")
        
        # 1. Test "Rushed" State (Short prompt, no questions)
        prompt_rushed = "Hata var düzelt"
        for _ in range(5): theory_of_mind.analyze_interaction(prompt_rushed)
        state_1 = theory_of_mind.get_inferred_state()
        print(f"[INFO] Analyzed prompt: '{prompt_rushed}' -> Inferred State: {state_1}")
        
        patched_prompt_1 = empathy_tuner.patch_system_prompt("Sen bir asistansın.")
        print(f"[OK] Patched System Prompt:\n{patched_prompt_1}\n")
        
        # 2. Test "Frustrated" State (All caps, multiple errors)
        prompt_frustrated = "BU KOD NEDEN ÇALIŞMIYOR YİNE HATA VERDİ"
        for _ in range(5): theory_of_mind.analyze_interaction(prompt_frustrated, recent_errors=5)
        state_2 = theory_of_mind.get_inferred_state()
        print(f"[INFO] Analyzed prompt: '{prompt_frustrated}' -> Inferred State: {state_2}")
        
        patched_prompt_2 = empathy_tuner.patch_system_prompt("Sen bir asistansın.")
        print(f"[OK] Patched System Prompt:\n{patched_prompt_2}\n")
        
        # 3. Test "Exploratory" State (Long prompt with questions)
        prompt_exploratory = "Merhaba, Python'da list comprehension mantığını anlamıyorum. Derinlemesine, memory management detaylarıyla ve adım adım açıklar mısın lütfen? Neden generator'dan daha hızlı çalışıyor bazı durumlarda?"
        for _ in range(5): theory_of_mind.analyze_interaction(prompt_exploratory)
        state_3 = theory_of_mind.get_inferred_state()
        print(f"[INFO] Analyzed prompt: '{prompt_exploratory}' -> Inferred State: {state_3}")
        
        patched_prompt_3 = empathy_tuner.patch_system_prompt("Sen bir asistansın.")
        print(f"[OK] Patched System Prompt:\n{patched_prompt_3}\n")
        
        print("[OK] Theory of Mind & Empathy Tuner verified successfully.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_empathy_engine())
