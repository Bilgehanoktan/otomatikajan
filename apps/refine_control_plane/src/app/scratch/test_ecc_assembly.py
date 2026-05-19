import sys
import os

# Root dizini ekle
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
sys.path.append(root)

from services.orchestration.application.prompt_manager import prompt_manager
from services.orchestration.application.skill_catalog import skill_catalog
from services.orchestration.domain.models import ContextPackage

def test_integration():
    print("--- ECC Prompt Assembly Integration Test (Read-Only) ---")
    
    # 1. Skill Katalog Testi
    skills = skill_catalog.list_skills()
    print(f"[OK] Katalogda {len(skills)} skill var.")
    
    # 2. Otomatik Skill Seçimi Testi
    context_text = "api-design backend-patterns"
    selected_skills = skill_catalog.find_skills_by_context(context_text)
    print(f"[OK] Bağlam: '{context_text}'")
    print(f"     Seçilen Skill'ler: {selected_skills}")
    
    # 3. Prompt Assembly Testi
    ctx = ContextPackage(
        working_context="Testing ECC assembly logic.",
        selected_skill_ids=selected_skills,
        harness_profile="specialist"
    )
    
    assembled_prompt = prompt_manager.assemble_prompt(
        agent_id="test_agent",
        base_prompt="Sen bir test ajanısın.",
        context=ctx,
        task_context="Integration testing without LLM call."
    )
    
    print("\n--- Assembled Prompt Summary ---")
    print(f"Karakter Sayısı: {len(assembled_prompt)}")
    print("--- PROMPT START ---")
    print(assembled_prompt[:500])
    print("--- PROMPT END (PARTIAL) ---\n")
    print("İçerik Kontrolü:")
    
    checks = {
        "Governance Contract": "GOVERNANCE & QUALITY CONTRACT" in assembled_prompt,
        "Skill Metadata": "api-design" in assembled_prompt.lower(),
        "Task Context": "Integration testing" in assembled_prompt
    }
    
    for label, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")

if __name__ == "__main__":
    test_integration()
