import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_evolution_intelligence():
    print("--- AGI 20.0 & 21.0 Verification ---")
    
    try:
        from core.agi.learning.skill_synthesizer import skill_synthesizer
        from core.agi.cognitive.aesthetic_auditor import aesthetic_auditor
        
        print("[OK] AGI 20.0/21.0 components imported successfully.")
        
        # 1. Test Skill Synthesis (Weaver)
        # Mock DB session
        mock_db = MagicMock()
        
        created_skills = await skill_synthesizer.synthesize_from_wisdom(mock_db)
        if len(created_skills) > 0:
            print(f"[OK] Skill Weaver: Successfully synthesized {len(created_skills)} skills.")
            for s in created_skills:
                skill_path = os.path.join(".agent/skills", s, "SKILL.md")
                if os.path.exists(skill_path):
                    print(f"    - Skill created at: {skill_path}")
                else:
                    print(f"    - [WARN] Skill dir created but SKILL.md missing for {s}")
        else:
            print("[INFO] Skill Weaver: No new skills to synthesize (already exists or no wisdom).")

        # 2. Test Aesthetic Reflection (Visual Audit)
        audit_result = await aesthetic_auditor.audit_aesthetics()
        if audit_result.get("status") == "completed":
            print(f"[OK] Aesthetic Reflection: Audit completed.")
            print(f"    - Feedback excerpt: {audit_result['feedback'][:100]}...")
        else:
            print(f"[ERROR] Aesthetic Reflection failed: {audit_result}")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_evolution_intelligence())
